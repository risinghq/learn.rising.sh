import type { Env, Limits } from "./limits.ts";

export function reply(
  body: unknown,
  status = 200,
  headers: [string, string][] = [],
): Response {
  const response = Response.json(body, {
    status,
    headers: { "Cache-Control": "no-store" },
  });
  for (const [name, value] of headers) response.headers.append(name, value);
  return response;
}

export function redirect(location: string, cookies: string[] = []): Response {
  const headers = new Headers({
    Location: location,
    "Cache-Control": "no-store",
  });
  for (const cookie of cookies) headers.append("Set-Cookie", cookie);
  return new Response(null, { status: 302, headers });
}

export function fail(status: number, reason: string, error: string): Response {
  return reply({ error, reason }, status);
}

export interface ApiContext {
  request: Request;
  env: Env;
  limits: Limits;
  userId: string;
  now: number;
}

const TOO_LARGE = () =>
  fail(413, "too_large", "La petición es demasiado grande.");

export async function readJson(
  request: Request,
  maxBytes: number,
): Promise<unknown | Response> {
  if (!request.headers.get("content-type")?.startsWith("application/json")) {
    return fail(415, "content_type", "Usa Content-Type: application/json.");
  }
  if (Number(request.headers.get("content-length")) > maxBytes)
    return TOO_LARGE();
  const bytes = new Uint8Array(await request.arrayBuffer());
  if (bytes.length > maxBytes) return TOO_LARGE();
  try {
    return JSON.parse(new TextDecoder().decode(bytes));
  } catch {
    return fail(400, "bad_request", "La petición no es un JSON válido.");
  }
}

export const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

// A request that changes data counts only if the page is from this same origin.
export function sameOrigin(request: Request): boolean {
  return request.headers.get("origin") === new URL(request.url).origin;
}
