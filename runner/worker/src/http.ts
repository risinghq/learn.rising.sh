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

// A request that changes data counts only if the page is from this same origin.
export function sameOrigin(request: Request): boolean {
  return request.headers.get("origin") === new URL(request.url).origin;
}
