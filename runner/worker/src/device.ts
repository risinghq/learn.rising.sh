import {
  newCliToken,
  randomToken,
  sessionUser,
  sha256,
  unixSeconds,
} from "./account.ts";
import { newCode, normalized } from "./friends.ts";
import { fail, isRecord, readJson, reply, sameOrigin } from "./http.ts";
import type { Env, Limits } from "./limits.ts";

// The device flow (RFC 8628) that logs the command line in. The CLI asks for a
// pair of codes, the learner approves the short one in a browser that is signed
// in, and the CLI collects a token with the long one.

const CODE_MS = 10 * 60_000;
// The CLI waits this long between two polls; sooner gets 429 `slow_down`.
const INTERVAL_SECONDS = 5;
const USER_CODE_CHARS = 8;
const MAX_BODY_BYTES = 500;
const MAX_DEVICE_CODE_CHARS = 100;
const MAX_FORM_BYTES = 1000;
// ALPHABET of friends.ts, shaped as it is displayed.
const USER_CODE = /^[A-HJKMNP-Z2-9]{4}-[A-HJKMNP-Z2-9]{4}$/;

interface Context {
  request: Request;
  env: Env;
  limits: Limits;
  now: number;
}

export interface DeviceRoute {
  method: "GET" | "POST";
  // A poll is bounded by its interval, so it skips the per-IP counter that
  // would stop a CLI polling every 5 seconds.
  counted: boolean;
  handle: (context: Context) => Promise<Response>;
}

const SECURITY_HEADERS = {
  "Content-Type": "text/html; charset=utf-8",
  "Cache-Control": "no-store",
  // The approve button must not be framed by another site.
  "Content-Security-Policy":
    "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
  "Referrer-Policy": "no-referrer",
  "X-Content-Type-Options": "nosniff",
};

const STYLE = `body{font:16px/1.5 system-ui,sans-serif;max-width:28rem;margin:4rem auto;padding:0 1rem;color-scheme:light dark}
code{font-size:2rem;letter-spacing:.1em;display:block;margin:1rem 0}
button,a.button,input{font:inherit;padding:.5rem 1rem;margin:.25rem .25rem .25rem 0}
a.button{display:inline-block;border:1px solid;border-radius:.25rem;color:inherit;text-decoration:none}`;

function html(title: string, body: string, status = 200): Response {
  return new Response(
    `<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>${title}</title><style>${STYLE}</style><main><h1>${title}</h1>${body}</main></html>`,
    { status, headers: SECURITY_HEADERS },
  );
}

const TITLE = "Conectar la terminal";

// The displayed form of a code the learner typed, or null if it cannot be one.
// Only characters of the alphabet survive, so it is safe to put in a page.
function userCodeOf(text: string | null): string | null {
  if (text === null) return null;
  const chars = normalized(text);
  if (chars.length !== USER_CODE_CHARS) return null;
  const shown = `${chars.slice(0, 4)}-${chars.slice(4)}`;
  return USER_CODE.test(shown) ? shown : null;
}

const userHash = (code: string) => sha256(normalized(code));

type State = "pending" | "unknown" | "expired" | "decided";

async function stateOf(
  db: D1Database,
  code: string,
  now: number,
): Promise<State> {
  const row = await db
    .prepare(
      "SELECT expires_at, decision FROM device_codes WHERE user_hash = ?1",
    )
    .bind(await userHash(code))
    .first<{ expires_at: number; decision: string | null }>();
  if (!row) return "unknown";
  if (row.expires_at <= unixSeconds(now)) return "expired";
  return row.decision === null ? "pending" : "decided";
}

const REFUSALS: Record<Exclude<State, "pending">, [number, string]> = {
  unknown: [
    404,
    "Ese código no existe. Revisa que sea el que muestra la terminal.",
  ],
  expired: [410, "Ese código venció. Ejecuta `rising login` otra vez."],
  decided: [409, "Ese código ya se usó."],
};

function refusal(state: Exclude<State, "pending">): Response {
  const [status, text] = REFUSALS[state];
  return html(TITLE, `<p>${text}</p>`, status);
}

function signInLinks(code: string | null): string {
  const back = encodeURIComponent(
    code ? `/auth/device?code=${code}` : "/auth/device",
  );
  return `<p>Inicia sesión para aprobar el acceso.</p>
<a class="button" href="/auth/google?return=${back}">Entrar con Google</a>
<a class="button" href="/auth/github?return=${back}">Entrar con GitHub</a>`;
}

async function createCode({ request, env, now }: Context): Promise<Response> {
  const deviceCode = randomToken(32);
  const expiresAt = unixSeconds(now + CODE_MS);
  // Take over the row of an expired code if the new one collides with it. A
  // live collision changes nothing and a new code is drawn.
  const deviceHash = await sha256(deviceCode);
  const draws = await Promise.all(
    Array.from({ length: 5 }, async () => {
      const userCode = newCode(USER_CODE_CHARS);
      return { userCode, hash: await userHash(userCode) };
    }),
  );
  for (const { userCode, hash } of draws) {
    // oxlint-disable-next-line eslint/no-await-in-loop -- Each draw depends on the last outcome.
    const stored = await env.DB.prepare(
      `INSERT INTO device_codes (device_hash, user_hash, expires_at)
       VALUES (?1, ?2, ?3)
       ON CONFLICT (user_hash) DO UPDATE SET
         device_hash = excluded.device_hash, expires_at = excluded.expires_at,
         polled_at = 0, user_id = NULL, decision = NULL
       WHERE device_codes.expires_at <= ?4`,
    )
      .bind(deviceHash, hash, expiresAt, unixSeconds(now))
      .run();
    if (stored.meta.changes === 1) {
      const approvalPage = `${new URL(request.url).origin}/auth/device`;
      return reply({
        deviceCode,
        userCode,
        verificationUri: approvalPage,
        verificationUriComplete: `${approvalPage}?code=${userCode}`,
        expiresIn: CODE_MS / 1000,
        interval: INTERVAL_SECONDS,
      });
    }
  }
  return fail(503, "busy", "No se pudo crear un código. Inténtalo de nuevo.");
}

async function pollToken({
  request,
  env,
  limits,
  now,
}: Context): Promise<Response> {
  const body = await readJson(request, MAX_BODY_BYTES);
  if (body instanceof Response) return body;
  if (
    !isRecord(body) ||
    typeof body.deviceCode !== "string" ||
    body.deviceCode.length > MAX_DEVICE_CODE_CHARS
  )
    return fail(400, "bad_request", "Falta deviceCode.");
  const db = env.DB;
  const hash = await sha256(body.deviceCode);
  const row = await db
    .prepare(
      "SELECT expires_at, decision FROM device_codes WHERE device_hash = ?1",
    )
    .bind(hash)
    .first<{ expires_at: number; decision: string | null }>();
  if (!row)
    return fail(400, "invalid_code", "Ese código no existe o ya se usó.");
  if (row.expires_at <= unixSeconds(now)) {
    await db
      .prepare("DELETE FROM device_codes WHERE device_hash = ?1")
      .bind(hash)
      .run();
    return fail(400, "expired_code", "El código venció. Empieza de nuevo.");
  }
  // One statement tests the interval and records the poll, so concurrent polls
  // cannot both pass.
  const polled = await db
    .prepare(
      "UPDATE device_codes SET polled_at = ?2 WHERE device_hash = ?1 AND polled_at <= ?3",
    )
    .bind(hash, now, now - INTERVAL_SECONDS * 1000)
    .run();
  if (polled.meta.changes === 0) {
    const response = fail(429, "slow_down", "Consulta con menos frecuencia.");
    response.headers.set("Retry-After", String(INTERVAL_SECONDS));
    return response;
  }
  if (row.decision === null)
    return fail(400, "authorization_pending", "Falta que apruebes el código.");
  if (row.decision === "denied") {
    await db
      .prepare("DELETE FROM device_codes WHERE device_hash = ?1")
      .bind(hash)
      .run();
    return fail(403, "access_denied", "Rechazaste el acceso.");
  }
  const token = newCliToken();
  const expiresAt = now + limits.cliTokenMs;
  // The token and the end of the code are one batch: of two polls that both
  // read "approved", only the first finds the row.
  const [issued] = await db.batch([
    db
      .prepare(
        `INSERT INTO sessions (token_hash, user_id, expires_at, kind)
         SELECT ?2, user_id, ?3, 'cli' FROM device_codes
         WHERE device_hash = ?1 AND decision = 'approved'`,
      )
      .bind(hash, await sha256(token), unixSeconds(expiresAt)),
    db
      .prepare(
        "DELETE FROM device_codes WHERE device_hash = ?1 AND decision = 'approved'",
      )
      .bind(hash),
  ]);
  if (issued.meta.changes !== 1)
    return fail(400, "invalid_code", "Ese código no existe o ya se usó.");
  return reply({ token, expiresAt: unixSeconds(expiresAt) * 1000 });
}

async function page({ request, env, now }: Context): Promise<Response> {
  const raw = new URL(request.url).searchParams.get("code");
  const code = userCodeOf(raw);
  const userId = await sessionUser(env.DB, request.headers.get("cookie"), now);
  if (!userId) return html(TITLE, signInLinks(code));
  if (code === null) {
    const note = raw ? "<p>Ese código no tiene el formato correcto.</p>" : "";
    return html(
      TITLE,
      `${note}<form method="get" action="/auth/device">
<label>Código que muestra la terminal<br><input name="code" maxlength="9" autocomplete="off" autofocus required></label>
<button>Continuar</button></form>`,
      raw ? 400 : 200,
    );
  }
  const state = await stateOf(env.DB, code, now);
  if (state !== "pending") return refusal(state);
  return html(
    TITLE,
    `<p>¿La terminal muestra este código?</p><code>${code}</code>
<p>Aprueba solo si lo pediste tú.</p>
<form method="post" action="/auth/device/approve"><input type="hidden" name="code" value="${code}">
<button name="decision" value="approve">Aprobar</button>
<button name="decision" value="deny">Rechazar</button></form>`,
  );
}

async function decide({ request, env, now }: Context): Promise<Response> {
  if (!sameOrigin(request))
    return fail(403, "bad_origin", "Origen no permitido.");
  const userId = await sessionUser(env.DB, request.headers.get("cookie"), now);
  if (!userId) return html(TITLE, signInLinks(null), 401);
  if (Number(request.headers.get("content-length")) > MAX_FORM_BYTES)
    return fail(413, "too_large", "La petición es demasiado grande.");
  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return fail(400, "bad_request", "El formulario no es válido.");
  }
  const code = userCodeOf(String(form.get("code") ?? ""));
  const decision = { approve: "approved", deny: "denied" }[
    String(form.get("decision"))
  ];
  if (!code || !decision)
    return fail(400, "bad_request", "Faltan el código o la decisión.");
  const stored = await env.DB.prepare(
    `UPDATE device_codes SET user_id = ?1, decision = ?2
     WHERE user_hash = ?3 AND decision IS NULL AND expires_at > ?4`,
  )
    .bind(userId, decision, await userHash(code), unixSeconds(now))
    .run();
  if (stored.meta.changes === 0) {
    const state = await stateOf(env.DB, code, now);
    // Another request decided it between the update and this read.
    return refusal(state === "pending" ? "decided" : state);
  }
  return html(
    TITLE,
    decision === "approved"
      ? "<p>Listo. Vuelve a la terminal.</p>"
      : "<p>Rechazado. La terminal no recibirá acceso.</p>",
  );
}

const ROUTES: Record<string, DeviceRoute> = {
  "": { method: "GET", counted: true, handle: page },
  code: { method: "POST", counted: true, handle: createCode },
  token: { method: "POST", counted: false, handle: pollToken },
  approve: { method: "POST", counted: true, handle: decide },
};

export const deviceRoute = (step = ""): DeviceRoute | undefined =>
  Object.hasOwn(ROUTES, step) ? ROUTES[step] : undefined;
