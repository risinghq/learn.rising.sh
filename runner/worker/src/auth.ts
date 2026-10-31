import {
  DAY_MS,
  type Provider,
  base64url,
  bearerToken,
  fromBase64url,
  clearedCookie,
  closeSession,
  openSession,
  randomToken,
  revokeCliToken,
  userForIdentity,
} from "./account.ts";
import { deviceRoute } from "./device.ts";
import { fail, redirect, sameOrigin } from "./http.ts";
import type { Env, Limits } from "./limits.ts";
import type { RateLimiter } from "./meters.ts";
import { getCookie } from "./session.ts";
import { take } from "./throttle.ts";

const FLOW_COOKIE = "qg_oauth";
const FLOW_SECONDS = 600;
const PROVIDER_TIMEOUT_MS = 5000;
const MAX_SUBJECT_CHARS = 255;
// GitHub rejects API requests without a User-Agent. It is a fixed text: it says
// nothing about who runs the site.
const USER_AGENT = "qiskit-guides";

interface ProviderConfig {
  authorize: string;
  token: string;
  userinfo: string;
  // Only the learner's identifier is requested: no email, no name.
  scope?: string;
  credentials(env: Env): { id?: string; secret?: string };
  subject(info: Record<string, unknown>): string | null;
}

const PROVIDERS: Record<Provider, ProviderConfig> = {
  google: {
    authorize: "https://accounts.google.com/o/oauth2/v2/auth",
    token: "https://oauth2.googleapis.com/token",
    userinfo: "https://openidconnect.googleapis.com/v1/userinfo",
    scope: "openid",
    credentials: (env) => ({
      id: env.GOOGLE_CLIENT_ID,
      secret: env.GOOGLE_CLIENT_SECRET,
    }),
    subject: (info) => (typeof info.sub === "string" ? info.sub : null),
  },
  github: {
    authorize: "https://github.com/login/oauth/authorize",
    token: "https://github.com/login/oauth/access_token",
    userinfo: "https://api.github.com/user",
    credentials: (env) => ({
      id: env.GITHUB_CLIENT_ID,
      secret: env.GITHUB_CLIENT_SECRET,
    }),
    subject: (info) => (Number.isSafeInteger(info.id) ? String(info.id) : null),
  },
};

const isProvider = (name: string): name is Provider =>
  Object.hasOwn(PROVIDERS, name);

// What travels in the `qg_oauth` cookie between leaving for the provider and coming back.
interface Flow {
  provider: Provider;
  state: string;
  verifier: string;
  next: string;
}

// Only a path of this site: it starts with a single "/" and has no "\" or
// control characters. "//host" and "/\host" leave the site in browsers.
export function localPath(value: string | null): string | null {
  if (value === null || value === "") return "/";
  // oxlint-disable-next-line no-control-regex -- control characters are exactly what is rejected
  if (value.length > 200 || !/^\/(?![/\\])[^\\\x00-\x20\x7f]*$/.test(value))
    return null;
  return value;
}

// A `Location` header carries only ASCII: the rest is percent-encoded, in UTF-8.
const asciiPath = (path: string) =>
  path.replace(/\P{ASCII}+/gu, (run) =>
    Array.from(
      new TextEncoder().encode(run),
      (byte) => `%${byte.toString(16).toUpperCase().padStart(2, "0")}`,
    ).join(""),
  );

const flowCookie = (value: string, maxAge: number) =>
  `${FLOW_COOKIE}=${value}; Max-Age=${maxAge}; Path=/auth; HttpOnly; Secure; SameSite=Lax`;

function readFlow(cookieHeader: string | null): Flow | null {
  const raw = getCookie(cookieHeader, FLOW_COOKIE);
  if (!raw) return null;
  try {
    const flow = JSON.parse(
      new TextDecoder().decode(fromBase64url(raw)),
    ) as Flow;
    const strings = [flow.provider, flow.state, flow.verifier, flow.next];
    // `next` is validated again: the browser carries the cookie and it may arrive altered.
    return strings.every((part) => typeof part === "string") &&
      isProvider(flow.provider) &&
      localPath(flow.next) !== null
      ? flow
      : null;
  } catch {
    return null;
  }
}

const sameText = (a: string, b: string) =>
  a.length === b.length &&
  crypto.subtle.timingSafeEqual(
    new TextEncoder().encode(a),
    new TextEncoder().encode(b),
  );

async function start(
  request: Request,
  env: Env,
  provider: Provider,
): Promise<Response> {
  const config = PROVIDERS[provider];
  const { id, secret } = config.credentials(env);
  if (!id || !secret) {
    return fail(
      503,
      "provider_unavailable",
      "Este proveedor de inicio de sesión no está configurado.",
    );
  }
  const url = new URL(request.url);
  const next = localPath(url.searchParams.get("return"));
  if (next === null) {
    return fail(
      400,
      "bad_return",
      "La dirección de regreso no es una ruta de este sitio.",
    );
  }
  const flow: Flow = {
    provider,
    state: randomToken(16),
    verifier: randomToken(32),
    next,
  };
  const target = new URL(config.authorize);
  target.search = new URLSearchParams({
    client_id: id,
    redirect_uri: `${url.origin}/auth/${provider}/callback`,
    response_type: "code",
    state: flow.state,
    code_challenge: base64url(
      new Uint8Array(
        await crypto.subtle.digest(
          "SHA-256",
          new TextEncoder().encode(flow.verifier),
        ),
      ),
    ),
    code_challenge_method: "S256",
    ...(config.scope && { scope: config.scope }),
  }).toString();
  const cookie = base64url(new TextEncoder().encode(JSON.stringify(flow)));
  return redirect(target.toString(), [flowCookie(cookie, FLOW_SECONDS)]);
}

type Exchange = { subject: string } | "rejected" | "unavailable";

// Exchange the code for a token and read the learner's identifier from the provider.
async function exchange(
  env: Env,
  provider: Provider,
  origin: string,
  code: string,
  verifier: string,
): Promise<Exchange> {
  const config = PROVIDERS[provider];
  const { id, secret } = config.credentials(env);
  const headers = { Accept: "application/json", "User-Agent": USER_AGENT };
  try {
    const tokenResponse = await fetch(config.token, {
      method: "POST",
      headers,
      body: new URLSearchParams({
        grant_type: "authorization_code",
        code,
        redirect_uri: `${origin}/auth/${provider}/callback`,
        client_id: id ?? "",
        client_secret: secret ?? "",
        code_verifier: verifier,
      }),
      signal: AbortSignal.timeout(PROVIDER_TIMEOUT_MS),
    });
    if (tokenResponse.status >= 500) return "unavailable";
    // GitHub answers 200 with `error` when it rejects the code.
    const token = (await tokenResponse.json().catch(() => null)) as {
      access_token?: unknown;
    } | null;
    if (!tokenResponse.ok || typeof token?.access_token !== "string")
      return "rejected";

    const infoResponse = await fetch(config.userinfo, {
      headers: { ...headers, Authorization: `Bearer ${token.access_token}` },
      signal: AbortSignal.timeout(PROVIDER_TIMEOUT_MS),
    });
    if (infoResponse.status >= 500) return "unavailable";
    if (!infoResponse.ok) return "rejected";
    const info = (await infoResponse.json().catch(() => null)) as Record<
      string,
      unknown
    > | null;
    const subject = info ? config.subject(info) : null;
    return subject && subject.length <= MAX_SUBJECT_CHARS
      ? { subject }
      : "rejected";
  } catch {
    return "unavailable";
  }
}

async function callback(
  request: Request,
  env: Env,
  limits: Limits,
  provider: Provider,
  now: number,
): Promise<Response> {
  const url = new URL(request.url);
  const flow = readFlow(request.headers.get("cookie"));
  const spent = [flowCookie("", 0)];
  const refuse = (status: number, reason: string, error: string) => {
    const response = fail(status, reason, error);
    response.headers.append("Set-Cookie", spent[0]);
    return response;
  };
  if (!flow || flow.provider !== provider) {
    return refuse(
      400,
      "flow_missing",
      "El inicio de sesión caducó. Vuelve a intentarlo desde la página.",
    );
  }
  const state = url.searchParams.get("state");
  if (state === null || !sameText(state, flow.state)) {
    return refuse(
      400,
      "state_mismatch",
      "El inicio de sesión no coincide con el que empezaste.",
    );
  }
  if (url.searchParams.has("error")) {
    // The learner cancelled on the provider's screen.
    return redirect(asciiPath(flow.next), spent);
  }
  const code = url.searchParams.get("code");
  if (!code || code.length > 2048) {
    return refuse(400, "code_missing", "El proveedor no devolvió un código.");
  }

  const result = await exchange(env, provider, url.origin, code, flow.verifier);
  if (result === "unavailable") {
    return refuse(
      502,
      "provider_failed",
      "El proveedor no respondió. Inténtalo de nuevo en unos segundos.",
    );
  }
  if (result === "rejected") {
    return refuse(
      400,
      "code_rejected",
      "El proveedor rechazó el inicio de sesión. Vuelve a empezar.",
    );
  }
  const userId = await userForIdentity(env.DB, provider, result.subject, now);
  await env.DB.prepare(
    "UPDATE users SET seen_day = MAX(seen_day, ?1) WHERE id = ?2",
  )
    .bind(Math.floor(now / DAY_MS), userId)
    .run();
  const session = await openSession(env.DB, userId, now, limits.authSessionMs);
  return redirect(asciiPath(flow.next), [session, ...spent]);
}

export async function handleAuth(
  request: Request,
  env: Env,
  limits: Limits,
  limiters: DurableObjectNamespace<RateLimiter>,
  now: number,
): Promise<Response> {
  const [, name = "", extra, tail] = new URL(request.url).pathname
    .split("/")
    .filter(Boolean);
  let route: "logout" | "start" | "callback" | null = null;
  const device =
    name === "device" && tail === undefined ? deviceRoute(extra) : undefined;
  if (tail === undefined) {
    if (name === "logout" && extra === undefined) route = "logout";
    else if (isProvider(name) && extra === undefined) route = "start";
    else if (isProvider(name) && extra === "callback") route = "callback";
  }
  if (!route && !device) return fail(404, "not_found", "No existe.");
  const method = device ? device.method : route === "logout" ? "POST" : "GET";
  if (request.method !== method) {
    const response = fail(405, "method", `Usa ${method}.`);
    response.headers.set("Allow", method);
    return response;
  }

  if (!device || device.counted) {
    const ip = request.headers.get("cf-connecting-ip") ?? "";
    const verdict = await take(
      limiters,
      env.TURNSTILE_SECRET,
      "auth",
      ip,
      now,
      limits.authPerMinute,
      limits.perDay,
    );
    if (!verdict.ok) {
      const response = fail(
        429,
        "rate_auth",
        "Demasiados intentos de inicio de sesión. Espera un minuto.",
      );
      response.headers.set("Retry-After", String(verdict.retryAfter));
      return response;
    }
  }

  if (device) return device.handle({ request, env, limits, now });
  if (route === "logout") {
    // Bearer logout does not use the browser's origin check and revokes its token.
    const bearer = bearerToken(request);
    if (bearer !== undefined) {
      await revokeCliToken(env.DB, bearer);
    } else {
      if (!sameOrigin(request))
        return fail(403, "bad_origin", "Origen no permitido.");
      await closeSession(env.DB, request.headers.get("cookie"));
    }
    return new Response(null, {
      status: 204,
      headers: { "Set-Cookie": clearedCookie(), "Cache-Control": "no-store" },
    });
  }
  return route === "start"
    ? start(request, env, name as Provider)
    : callback(request, env, limits, name as Provider, now);
}
