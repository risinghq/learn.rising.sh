import { DAY_MS, sha256, unixSeconds } from "./account.ts";
import { type ApiContext, fail, isRecord, readJson, reply } from "./http.ts";
import { streakFor, streaksOf, weekOf, weeklyXp } from "./xp.ts";

const MAX_BODY_BYTES = 500;
const INVITE_MS = 7 * DAY_MS;
const MAX_OPEN_INVITES = 5;

// Exclude I, L, and O because they resemble 1 and 0.
const ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";
const CODE_CHARS = 10;

// A code of `length` characters from ALPHABET with a dash in the middle.
export function newCode(length = CODE_CHARS): string {
  const chars: string[] = [];
  // Reject the incomplete range so each alphabet character is equally likely.
  const limit = 256 - (256 % ALPHABET.length);
  while (chars.length < length) {
    for (const byte of crypto.getRandomValues(new Uint8Array(length))) {
      if (byte < limit && chars.length < length)
        chars.push(ALPHABET[byte % ALPHABET.length]);
    }
  }
  const half = length / 2;
  return `${chars.slice(0, half).join("")}-${chars.slice(half).join("")}`;
}

// Removes separators and case from a user-entered code.
export const normalized = (code: string) =>
  code.replaceAll(/[\s-]/g, "").toUpperCase();

export async function postInvite({
  env,
  userId,
  now,
}: ApiContext): Promise<Response> {
  const code = newCode();
  const expiresAt = now + INVITE_MS;
  // The count and the insert are one statement, so racing requests cannot
  // open more than the cap.
  const inserted = await env.DB.prepare(
    `INSERT INTO friend_invites (code_hash, user_id, expires_at)
     SELECT ?1, ?2, ?3
     WHERE (
       SELECT COUNT(*) FROM friend_invites
       WHERE user_id = ?2 AND used_at IS NULL AND expires_at > ?4
     ) < ?5`,
  )
    .bind(
      await sha256(normalized(code)),
      userId,
      unixSeconds(expiresAt),
      unixSeconds(now),
      MAX_OPEN_INVITES,
    )
    .run();
  if (inserted.meta.changes === 0) {
    return fail(
      429,
      "too_many_invites",
      "Ya tienes varios códigos sin usar. Espera a que se usen o venzan.",
    );
  }
  return reply({ code, expiresAt: unixSeconds(expiresAt) * 1000 });
}

// Why an accept found nothing to do, read after the fact.
async function whyRefused(
  db: D1Database,
  hash: string,
  userId: string,
  seconds: number,
  maxFriends: number,
): Promise<Response> {
  const invite = await db
    .prepare(
      "SELECT user_id, expires_at, used_at FROM friend_invites WHERE code_hash = ?1",
    )
    .bind(hash)
    .first<{ user_id: string; expires_at: number; used_at: number | null }>();
  if (!invite) return fail(404, "invite_unknown", "Ese código no existe.");
  if (invite.used_at !== null)
    return fail(410, "invite_used", "Ese código ya se usó.");
  if (invite.expires_at <= seconds)
    return fail(410, "invite_expired", "Ese código venció.");
  if (invite.user_id === userId)
    return fail(400, "own_code", "No puedes usar tu propio código.");
  const already = await db
    .prepare(
      "SELECT 1 AS found FROM friendships WHERE user_id = ?1 AND friend_id = ?2",
    )
    .bind(userId, invite.user_id)
    .first();
  if (already) return fail(409, "already_friends", "Ya son amigos.");
  return fail(
    409,
    "friend_limit",
    `Una cuenta admite hasta ${maxFriends} amigos.`,
  );
}

export async function postAccept({
  request,
  env,
  limits,
  userId,
  now,
}: ApiContext): Promise<Response> {
  const body = await readJson(request, MAX_BODY_BYTES);
  if (body instanceof Response) return body;
  if (!isRecord(body) || typeof body.code !== "string")
    return fail(400, "bad_request", "Falta el campo code.");
  const code = normalized(body.code);
  if (code.length !== CODE_CHARS)
    return fail(400, "bad_request", "El código no tiene el formato correcto.");
  const db = env.DB;
  const hash = await sha256(code);
  const seconds = unixSeconds(now);

  // The friendship, both limits and the spending of the code are one batch,
  // so racing accepts cannot exceed a limit, repeat a pair or spend a code
  // twice. The first statement inserts both sides only when the code is open,
  // the pair is new and neither side is full; the second spends the code only
  // if the first inserted.
  const [linked] = await db.batch<{ id: number; user_id: string }>([
    db
      .prepare(
        `WITH invite AS (
           SELECT user_id AS owner FROM friend_invites
           WHERE code_hash = ?1 AND used_at IS NULL AND expires_at > ?3
             AND user_id <> ?2
         )
         INSERT INTO friendships (user_id, friend_id, since)
         SELECT side.a, side.b, ?3 FROM (
           SELECT ?2 AS a, owner AS b FROM invite
           UNION ALL SELECT owner, ?2 FROM invite
         ) AS side
         WHERE NOT EXISTS (
             SELECT 1 FROM friendships
             WHERE user_id = ?2 AND friend_id = (SELECT owner FROM invite)
           )
           AND (SELECT COUNT(*) FROM friendships WHERE user_id = ?2) < ?4
           AND (
             SELECT COUNT(*) FROM friendships
             WHERE user_id = (SELECT owner FROM invite)
           ) < ?4
         RETURNING id, user_id`,
      )
      .bind(hash, userId, seconds, limits.maxFriends),
    db
      .prepare(
        `UPDATE friend_invites SET used_at = ?2
         WHERE code_hash = ?1 AND used_at IS NULL AND changes() > 0`,
      )
      .bind(hash, seconds),
  ]);
  const mine = linked.results.find((row) => row.user_id === userId);
  if (!mine) return whyRefused(db, hash, userId, seconds, limits.maxFriends);
  return reply({ id: mine.id });
}

export async function getFriends({
  env,
  userId,
  now,
}: ApiContext): Promise<Response> {
  const db = env.DB;
  const rows = await db
    .prepare(
      `SELECT f.id, f.friend_id, u.time_zone
       FROM friendships f JOIN users u ON u.id = f.friend_id
       WHERE f.user_id = ?1 ORDER BY f.id`,
    )
    .bind(userId)
    .all<{ id: number; friend_id: string; time_zone: string }>();
  const ids = rows.results.map((row) => row.friend_id);
  const [streaks, totals] = await Promise.all([
    streaksOf(db, ids),
    weekOf(db, userId, now).then((week) => weeklyXp(db, ids, week)),
  ]);
  return reply({
    friends: rows.results.map((row) => {
      const { current, today } = streakFor(
        streaks,
        row.friend_id,
        row.time_zone,
        now,
      );
      return {
        id: row.id,
        streak: current,
        today,
        xp: totals.get(row.friend_id) ?? 0,
      };
    }),
  });
}

export async function deleteFriend(
  { env, userId }: ApiContext,
  id: string,
): Promise<Response> {
  const db = env.DB;
  const friend = await db
    .prepare("SELECT friend_id FROM friendships WHERE id = ?1 AND user_id = ?2")
    .bind(id, userId)
    .first<string>("friend_id");
  if (friend === null) return fail(404, "not_found", "No existe.");
  await db
    .prepare(
      `DELETE FROM friendships
       WHERE (user_id = ?1 AND friend_id = ?2) OR (user_id = ?2 AND friend_id = ?1)`,
    )
    .bind(userId, friend)
    .run();
  return new Response(null, { status: 204 });
}
