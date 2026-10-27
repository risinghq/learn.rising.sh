const COOKIE = "qg_session";
const TURNSTILE_URL =
  "https://challenges.cloudflare.com/turnstile/v0/siteverify";
const MAX_TOKEN_CHARS = 2048;

const encoder = new TextEncoder();

function hex(bytes: ArrayBuffer): string {
  return [...new Uint8Array(bytes)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

// HMAC-SHA256 with a key derived from the Turnstile secret and a label,
// so the cookie and the limiter name do not share a key.
export async function mac(
  secret: string,
  label: string,
  message: string,
): Promise<string> {
  const root = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const derived = await crypto.subtle.sign("HMAC", root, encoder.encode(label));
  const key = await crypto.subtle.importKey(
    "raw",
    derived,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  return hex(await crypto.subtle.sign("HMAC", key, encoder.encode(message)));
}

// The cookie carries only the expiry time and a MAC that covers that time and the IP.
// No identifica a nadie y no sirve desde otra IP.
export async function issueSession(
  secret: string,
  ip: string,
  now: number,
  ttlMs: number,
): Promise<string> {
  const expires = Math.floor(now + ttlMs);
  const tag = await mac(secret, "session", `${expires}|${ip}`);
  const maxAge = Math.ceil(ttlMs / 1000);
  return `${COOKIE}=${expires}.${tag}; Max-Age=${maxAge}; Path=/run; HttpOnly; Secure; SameSite=Strict`;
}

export function getCookie(
  cookieHeader: string | null,
  name: string,
): string | undefined {
  return cookieHeader
    ?.split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${name}=`))
    ?.slice(name.length + 1);
}

export async function hasSession(
  secret: string,
  ip: string,
  now: number,
  cookieHeader: string | null,
): Promise<boolean> {
  const value = getCookie(cookieHeader, COOKIE);
  const [expires, tag] = value?.split(".") ?? [];
  if (!expires || !tag || !/^\d+$/.test(expires) || Number(expires) <= now)
    return false;
  const expected = await mac(secret, "session", `${expires}|${ip}`);
  return (
    expected.length === tag.length &&
    crypto.subtle.timingSafeEqual(encoder.encode(expected), encoder.encode(tag))
  );
}

export type Verification = "ok" | "rejected" | "unavailable";

// Only the secret and the token are sent; the learner's IP does not leave the Worker.
export async function verifyTurnstile(
  secret: string,
  token: string,
): Promise<Verification> {
  if (token.length > MAX_TOKEN_CHARS) return "rejected";
  try {
    const response = await fetch(TURNSTILE_URL, {
      method: "POST",
      body: new URLSearchParams({ secret, response: token }),
      signal: AbortSignal.timeout(5000),
    });
    if (!response.ok) return "unavailable";
    const result = (await response.json()) as { success?: boolean };
    return result.success === true ? "ok" : "rejected";
  } catch {
    return "unavailable";
  }
}
