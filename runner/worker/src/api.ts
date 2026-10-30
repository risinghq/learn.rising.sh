import { clearedCookie, sessionUser } from "./account.ts";
import { deleteFriend, getFriends, postAccept, postInvite } from "./friends.ts";
import { type ApiContext, fail, readJson, reply, sameOrigin } from "./http.ts";
import type { Env, Limits } from "./limits.ts";
import type { RateLimiter } from "./meters.ts";
import {
  Contended,
  Gone,
  TooMuch,
  mergeProgress,
  parseProgress,
  readProgress,
} from "./progress.ts";
import { take } from "./throttle.ts";
import { getBoard, getStreak, postXp } from "./xp.ts";

// D1 accepts 2 MB per bound value and the statement forwards the body with another
// level of escapes; this cap leaves margin.
const MAX_BODY_BYTES = 800_000;

async function readProgressBody(request: Request) {
  const body = await readJson(request, MAX_BODY_BYTES);
  if (body instanceof Response) return body;
  const progress = parseProgress(body);
  return typeof progress === "string"
    ? fail(400, "bad_request", progress)
    : progress;
}

async function getMe({ env, userId }: ApiContext): Promise<Response> {
  const progress = await readProgress(env.DB, userId);
  if (!progress) return fail(401, "signed_out", "La cuenta ya no existe.");
  const providers = await env.DB.prepare(
    "SELECT provider FROM identities WHERE user_id = ?1 ORDER BY provider",
  )
    .bind(userId)
    .all<{ provider: string }>();
  return reply({
    signedIn: true,
    providers: providers.results.map((row) => row.provider),
    progress,
  });
}

async function deleteMe({ env, userId }: ApiContext): Promise<Response> {
  await env.DB.prepare("DELETE FROM users WHERE id = ?1").bind(userId).run();
  return reply({ deleted: true }, 200, [["Set-Cookie", clearedCookie()]]);
}

async function writeProgress(
  { request, env, userId, now }: ApiContext,
  merge: boolean,
): Promise<Response> {
  const incoming = await readProgressBody(request);
  if (incoming instanceof Response) return incoming;
  try {
    const merged = await mergeProgress(env.DB, userId, incoming, now);
    return merge
      ? reply({ progress: merged })
      : new Response(null, { status: 204 });
  } catch (error) {
    if (error instanceof TooMuch)
      return fail(
        413,
        "too_much",
        "Hay más progreso del que la cuenta admite.",
      );
    if (error instanceof Gone)
      return fail(401, "signed_out", "La cuenta ya no existe.");
    if (error instanceof Contended) {
      const response = fail(
        503,
        "busy",
        "La cuenta está ocupada. Inténtalo de nuevo.",
      );
      response.headers.set("Retry-After", "1");
      return response;
    }
    throw error;
  }
}

interface Route {
  method: "GET" | "POST" | "PUT" | "DELETE";
  path: RegExp;
  // The groups of `path` are the arguments after the context.
  handle: (context: ApiContext, ...params: string[]) => Promise<Response>;
}

const ROUTES: Route[] = [
  { method: "GET", path: /^\/api\/me$/, handle: getMe },
  { method: "DELETE", path: /^\/api\/me$/, handle: deleteMe },
  {
    method: "POST",
    path: /^\/api\/merge$/,
    handle: (context) => writeProgress(context, true),
  },
  {
    method: "PUT",
    path: /^\/api\/progress$/,
    handle: (context) => writeProgress(context, false),
  },
  { method: "POST", path: /^\/api\/xp$/, handle: postXp },
  { method: "GET", path: /^\/api\/streak$/, handle: getStreak },
  { method: "POST", path: /^\/api\/friends\/invite$/, handle: postInvite },
  { method: "POST", path: /^\/api\/friends\/accept$/, handle: postAccept },
  { method: "GET", path: /^\/api\/friends$/, handle: getFriends },
  {
    method: "DELETE",
    path: /^\/api\/friends\/([0-9]{1,15})$/,
    handle: deleteFriend,
  },
  { method: "GET", path: /^\/api\/board$/, handle: getBoard },
];

export async function handleApi(
  request: Request,
  env: Env,
  limits: Limits,
  limiters: DurableObjectNamespace<RateLimiter>,
  now: number,
): Promise<Response> {
  const { pathname } = new URL(request.url);
  const matches = ROUTES.filter((route) => route.path.test(pathname));
  if (matches.length === 0) return fail(404, "not_found", "No existe.");
  const route = matches.find((match) => match.method === request.method);
  if (!route) {
    const allowed = matches.map((match) => match.method).join(", ");
    const response = fail(405, "method", `Usa ${allowed}.`);
    response.headers.set("Allow", allowed);
    return response;
  }
  if (route.method !== "GET" && !sameOrigin(request))
    return fail(403, "bad_origin", "Origen no permitido.");

  const userId = await sessionUser(env.DB, request.headers.get("cookie"), now);
  if (!userId) {
    if (route.method === "GET" && pathname === "/api/me")
      return reply({ signedIn: false });
    return fail(401, "signed_out", "Inicia sesión para guardar tu progreso.");
  }
  const verdict = await take(
    limiters,
    env.TURNSTILE_SECRET,
    "api",
    userId,
    now,
    limits.perMinute,
    limits.perDay,
  );
  if (!verdict.ok) {
    const response = fail(
      429,
      `rate_${verdict.scope}`,
      "Demasiadas peticiones. Espera un momento.",
    );
    response.headers.set("Retry-After", String(verdict.retryAfter));
    return response;
  }

  const params = route.path.exec(pathname)!.slice(1);
  return route.handle({ request, env, limits, userId, now }, ...params);
}
