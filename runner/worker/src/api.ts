import { clearedCookie, sessionUser } from "./account.ts";
import { fail, reply, sameOrigin } from "./http.ts";
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

// D1 accepts 2 MB per bound value and the statement forwards the body with another
// level of escapes; this cap leaves margin.
const MAX_BODY_BYTES = 800_000;

async function readJson(request: Request): Promise<unknown | Response> {
  if (!request.headers.get("content-type")?.startsWith("application/json")) {
    return fail(415, "content_type", "Usa Content-Type: application/json.");
  }
  if (Number(request.headers.get("content-length")) > MAX_BODY_BYTES) {
    return fail(413, "too_large", "El progreso es demasiado grande.");
  }
  const bytes = new Uint8Array(await request.arrayBuffer());
  if (bytes.length > MAX_BODY_BYTES)
    return fail(413, "too_large", "El progreso es demasiado grande.");
  try {
    return JSON.parse(new TextDecoder().decode(bytes));
  } catch {
    return fail(400, "bad_request", "La petición no es un JSON válido.");
  }
}

async function readProgressBody(request: Request) {
  const body = await readJson(request);
  if (body instanceof Response) return body;
  const progress = parseProgress(body);
  return typeof progress === "string"
    ? fail(400, "bad_request", progress)
    : progress;
}

export async function handleApi(
  request: Request,
  env: Env,
  limits: Limits,
  limiters: DurableObjectNamespace<RateLimiter>,
  now: number,
): Promise<Response> {
  const { pathname } = new URL(request.url);
  const routes: Record<string, string> = {
    "/api/me": request.method === "DELETE" ? "DELETE" : "GET",
    "/api/merge": "POST",
    "/api/progress": "PUT",
  };
  const method = routes[pathname];
  if (!method) return fail(404, "not_found", "No existe.");
  if (request.method !== method) {
    const response = fail(405, "method", `Usa ${method}.`);
    response.headers.set("Allow", method);
    return response;
  }
  if (method !== "GET" && !sameOrigin(request))
    return fail(403, "bad_origin", "Origen no permitido.");

  const userId = await sessionUser(env.DB, request.headers.get("cookie"), now);
  if (!userId) {
    if (pathname === "/api/me" && method === "GET")
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

  if (pathname === "/api/me" && method === "GET") {
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

  if (pathname === "/api/me") {
    await env.DB.prepare("DELETE FROM users WHERE id = ?1").bind(userId).run();
    return reply({ deleted: true }, 200, [["Set-Cookie", clearedCookie()]]);
  }

  const incoming = await readProgressBody(request);
  if (incoming instanceof Response) return incoming;
  try {
    const merged = await mergeProgress(env.DB, userId, incoming, now);
    return pathname === "/api/merge"
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
