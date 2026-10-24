import { getCookie } from "./session.ts";

const COOKIE = "qg_auth";
export const DAY_MS = 86_400_000;
const MAX_TOKEN_CHARS = 100;

export const unixSeconds = (ms: number) => Math.floor(ms / 1000);

export function base64url(bytes: Uint8Array): string {
  let text = "";
  for (const byte of bytes) text += String.fromCharCode(byte);
  return btoa(text)
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replaceAll("=", "");
}

export function fromBase64url(text: string): Uint8Array {
  const binary = atob(text.replaceAll("-", "+").replaceAll("_", "/"));
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}

export const randomToken = (bytes: number) =>
  base64url(crypto.getRandomValues(new Uint8Array(bytes)));

export async function sha256(text: string): Promise<string> {
  return base64url(
    new Uint8Array(
      await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text)),
    ),
  );
}

// La cookie lleva un token al azar de 256 bits. La base guarda solo su hash, así
// que leer la tabla no da una sesión.
export async function openSession(
  db: D1Database,
  userId: string,
  now: number,
  ttlMs: number,
): Promise<string> {
  const token = randomToken(32);
  await db
    .prepare(
      "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?1, ?2, ?3)",
    )
    .bind(await sha256(token), userId, unixSeconds(now + ttlMs))
    .run();
  return `${COOKIE}=${token}; Max-Age=${Math.ceil(ttlMs / 1000)}; Path=/; HttpOnly; Secure; SameSite=Lax`;
}

export const clearedCookie = () =>
  `${COOKIE}=; Max-Age=0; Path=/; HttpOnly; Secure; SameSite=Lax`;

// El id del usuario de la cookie `qg_auth`, o null si no hay sesión vigente.
// Marca el día de la visita: la limpieza borra las cuentas sin visitas.
export async function sessionUser(
  db: D1Database,
  cookieHeader: string | null,
  now: number,
): Promise<string | null> {
  const token = getCookie(cookieHeader, COOKIE);
  if (!token || token.length > MAX_TOKEN_CHARS) return null;
  const row = await db
    .prepare(
      `SELECT s.user_id AS id, u.seen_day AS seen
       FROM sessions s JOIN users u ON u.id = s.user_id
       WHERE s.token_hash = ?1 AND s.expires_at > ?2`,
    )
    .bind(await sha256(token), unixSeconds(now))
    .first<{ id: string; seen: number }>();
  if (!row) return null;
  const day = Math.floor(now / DAY_MS);
  if (row.seen < day) {
    // La condición va en la sentencia: otra petición pudo marcar un día posterior.
    await db
      .prepare("UPDATE users SET seen_day = ?1 WHERE id = ?2 AND seen_day < ?1")
      .bind(day, row.id)
      .run();
  }
  return row.id;
}

// Si el usuario entró con una cuenta de GitHub cuyo id numérico está en `ids`.
// La base guarda ese id como `subject` de la identidad.
export async function isMaintainer(
  db: D1Database,
  userId: string,
  ids: string[],
): Promise<boolean> {
  if (ids.length === 0) return false;
  const row = await db
    .prepare(
      `SELECT 1 AS found FROM identities
       WHERE user_id = ?1 AND provider = 'github'
         AND subject IN (SELECT value FROM json_each(?2))`,
    )
    .bind(userId, JSON.stringify(ids))
    .first<{ found: number }>();
  return row !== null;
}

export async function closeSession(
  db: D1Database,
  cookieHeader: string | null,
): Promise<void> {
  const token = getCookie(cookieHeader, COOKIE);
  if (!token || token.length > MAX_TOKEN_CHARS) return;
  await db
    .prepare("DELETE FROM sessions WHERE token_hash = ?1")
    .bind(await sha256(token))
    .run();
}

export type Provider = "google" | "github";

export async function userForIdentity(
  db: D1Database,
  provider: Provider,
  subject: string,
  now: number,
): Promise<string> {
  const find = () =>
    db
      .prepare(
        "SELECT user_id FROM identities WHERE provider = ?1 AND subject = ?2",
      )
      .bind(provider, subject)
      .first<string>("user_id");
  const existing = await find();
  if (existing) return existing;
  const id = randomToken(16);
  const day = Math.floor(now / DAY_MS);
  try {
    await db.batch([
      db
        .prepare(
          "INSERT INTO users (id, created_day, seen_day) VALUES (?1, ?2, ?2)",
        )
        .bind(id, day),
      db
        .prepare(
          "INSERT INTO identities (provider, subject, user_id) VALUES (?1, ?2, ?3)",
        )
        .bind(provider, subject, id),
    ]);
    return id;
  } catch (error) {
    // Dos primeras entradas a la vez: la otra ganó y el lote entero se deshizo.
    const winner = await find();
    if (winner) return winner;
    throw error;
  }
}
