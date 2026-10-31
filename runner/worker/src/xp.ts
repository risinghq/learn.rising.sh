import { DAY_MS, unixSeconds } from "./account.ts";
import { EXERCISE } from "./contract.ts";
import { type ApiContext, fail, isRecord, readJson, reply } from "./http.ts";
import type { Limits } from "./limits.ts";
import { LESSON } from "./progress.ts";
import { FOLD_DAY, type Streak, type StreakRow, streakOf } from "./streak.ts";
import {
  canonicalZone,
  isoDate,
  localDay,
  mondayOf,
  startOfDay,
} from "./zone.ts";

const MAX_BODY_BYTES = 2000;

// `exercise` needs the server's recorded pass. `browser` is an exercise the page graded itself, so
// it has no record to check: it is bounded like `drill`, by the per-event and per-day caps.
const SOURCES = ["drill", "exercise", "browser", "lesson", "cli"] as const;
type Source = (typeof SOURCES)[number];

// Drill and CLI references use the same identifier grammar.
const ITEM = /^[A-Za-z0-9_.:-]{1,100}$/;
const REF: Record<Source, RegExp> = {
  drill: ITEM,
  cli: ITEM,
  exercise: EXERCISE,
  browser: EXERCISE,
  lesson: LESSON,
};

interface Award {
  source: Source;
  ref: string;
  amount: number;
  zone: string | null;
  /** When the XP was earned, in Unix milliseconds, if the client says. */
  earnedAt: number | null;
}

// A client may date an award up to this far back, so a post queued offline keeps its day.
const EARNED_WINDOW_MS = 2 * DAY_MS;

// Parses an award or returns its validation error.
function parseAward(body: unknown, limits: Limits): Award | string {
  if (!isRecord(body)) return "El cuerpo debe ser un objeto JSON.";
  const unknown = Object.keys(body).find(
    (key) => !["source", "ref", "amount", "tz", "earnedAt"].includes(key),
  );
  if (unknown) return `Campo desconocido: ${unknown.slice(0, 40)}.`;
  const { source, ref, amount, tz, earnedAt } = body;
  if (!SOURCES.includes(source as Source))
    return `source debe ser uno de: ${SOURCES.join(", ")}.`;
  if (typeof ref !== "string" || !REF[source as Source].test(ref))
    return `ref no es un id válido para ${source}.`;
  if (
    typeof amount !== "number" ||
    !Number.isInteger(amount) ||
    amount < 1 ||
    amount > limits.xpPerEvent
  )
    return `amount debe ser un entero entre 1 y ${limits.xpPerEvent}.`;
  let zone: string | null = null;
  if (tz !== undefined) {
    zone = typeof tz === "string" ? canonicalZone(tz) : null;
    if (!zone) return "tz debe ser un nombre de zona horaria IANA.";
  }
  if (
    earnedAt !== undefined &&
    (typeof earnedAt !== "number" || !Number.isSafeInteger(earnedAt))
  )
    return "earnedAt debe ser un entero en milisegundos.";
  return {
    source: source as Source,
    ref,
    amount,
    zone,
    earnedAt: earnedAt ?? null,
  };
}

async function zoneOf(db: D1Database, userId: string): Promise<string | null> {
  return db
    .prepare("SELECT time_zone FROM users WHERE id = ?1")
    .bind(userId)
    .first<string>("time_zone");
}

export async function postXp({
  request,
  env,
  limits,
  userId,
  now,
}: ApiContext): Promise<Response> {
  const body = await readJson(request, MAX_BODY_BYTES);
  if (body instanceof Response) return body;
  const award = parseAward(body, limits);
  if (typeof award === "string") return fail(400, "bad_request", award);
  const { source, ref, amount } = award;
  const db = env.DB;

  const stored = await zoneOf(db, userId);
  if (stored === null)
    return fail(401, "signed_out", "La cuenta ya no existe.");
  const zone = award.zone ?? stored;
  if (zone !== stored) {
    await db
      .prepare("UPDATE users SET time_zone = ?1 WHERE id = ?2")
      .bind(zone, userId)
      .run();
  }

  // Exercise XP requires the server's passing check, not a page-supplied state.
  if (source === "exercise") {
    const passed = await db
      .prepare(
        "SELECT 1 AS found FROM exercise_state WHERE user_id = ?1 AND exercise = ?2 AND passed = 1",
      )
      .bind(userId, ref)
      .first();
    if (!passed)
      return fail(
        403,
        "not_passed",
        "Aprueba la comprobación del ejercicio para ganar XP.",
      );
  }

  // The award belongs to the day it was earned, not the day it arrived, so a
  // resend that crosses midnight lands on the same day and is refused as a
  // repeat. A date outside the window, or none, is the arrival.
  const earned =
    award.earnedAt !== null &&
    award.earnedAt <= now &&
    award.earnedAt >= now - EARNED_WINDOW_MS
      ? award.earnedAt
      : now;
  const utcDay = Math.floor(earned / DAY_MS);
  // One statement stores the XP, so the cap and the once-per-day rule hold
  // when requests race: it inserts only the XP that still fits and only for a
  // new ref. The batch folds the day into the streak only if it stored XP.
  const [inserted] = await db.batch<{ amount: number }>([
    db
      .prepare(
        `INSERT INTO xp_events (user_id, at, utc_day, source, ref, amount)
         SELECT ?1, ?2, ?3, ?4, ?5, MIN(?6, ?7 - earned.total)
         FROM (
           SELECT COALESCE(SUM(amount), 0) AS total
           FROM xp_events WHERE user_id = ?1 AND utc_day = ?3
         ) AS earned
         WHERE earned.total < ?7
           AND NOT EXISTS (
             SELECT 1 FROM xp_events
             WHERE user_id = ?1 AND utc_day = ?3 AND source = ?4 AND ref = ?5
           )
         RETURNING amount`,
      )
      .bind(
        userId,
        unixSeconds(earned),
        utcDay,
        source,
        ref,
        amount,
        limits.xpPerDay,
      ),
    db.prepare(FOLD_DAY).bind(userId, localDay(earned, zone)),
  ]);
  const granted = inserted.results[0]?.amount ?? null;

  const total = await dayTotal(db, userId, utcDay);
  let reason: "ref_today" | "daily_cap" | null = null;
  if (granted === null) {
    const seen = await db
      .prepare(
        "SELECT 1 AS found FROM xp_events WHERE user_id = ?1 AND utc_day = ?2 AND source = ?3 AND ref = ?4",
      )
      .bind(userId, utcDay, source, ref)
      .first();
    reason = seen ? "ref_today" : "daily_cap";
  }
  return reply({
    granted: granted ?? 0,
    total,
    cap: limits.xpPerDay,
    reason,
  });
}

async function dayTotal(
  db: D1Database,
  userId: string,
  utcDay: number,
): Promise<number> {
  return (
    (await db
      .prepare(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM xp_events WHERE user_id = ?1 AND utc_day = ?2",
      )
      .bind(userId, utcDay)
      .first<number>("total")) ?? 0
  );
}

export async function getXp({
  env,
  limits,
  userId,
  now,
}: ApiContext): Promise<Response> {
  const db = env.DB;
  // `today` is the learner's own day, the one the streak counts. `total` is the
  // UTC day, the one the cap counts.
  const zone = (await zoneOf(db, userId)) ?? "UTC";
  const day = localDay(now, zone);
  const today = await db
    .prepare(
      `SELECT COALESCE(SUM(amount), 0) AS total FROM xp_events
       WHERE user_id = ?1 AND at >= ?2 AND at < ?3`,
    )
    .bind(
      userId,
      unixSeconds(startOfDay(day, zone)),
      unixSeconds(startOfDay(day + 1, zone)),
    )
    .first<number>("total");
  return reply({
    total: await dayTotal(db, userId, Math.floor(now / DAY_MS)),
    cap: limits.xpPerDay,
    today: today ?? 0,
  });
}

// Returns the streak row of each user that has one.
export async function streaksOf(
  db: D1Database,
  userIds: string[],
): Promise<Map<string, StreakRow>> {
  const rows = await db
    .prepare(
      `SELECT user_id, run, longest, freezes, last_day FROM streaks
       WHERE user_id IN (SELECT value FROM json_each(?1))`,
    )
    .bind(JSON.stringify(userIds))
    .all<StreakRow & { user_id: string }>();
  return new Map(rows.results.map((row) => [row.user_id, row]));
}

export function streakFor(
  rows: Map<string, StreakRow>,
  userId: string,
  zone: string,
  now: number,
): Streak {
  return streakOf(rows.get(userId), localDay(now, zone));
}

export async function getStreak({
  env,
  userId,
  now,
}: ApiContext): Promise<Response> {
  const zone = await zoneOf(env.DB, userId);
  if (zone === null) return fail(401, "signed_out", "La cuenta ya no existe.");
  return reply(streakFor(await streaksOf(env.DB, [userId]), userId, zone, now));
}

// Returns the user's ISO week and its UTC-second boundaries at `now`.
export async function weekOf(db: D1Database, userId: string, now: number) {
  const zone = (await zoneOf(db, userId)) ?? "UTC";
  const monday = mondayOf(localDay(now, zone));
  return {
    weekStart: isoDate(monday),
    from: unixSeconds(startOfDay(monday, zone)),
    to: unixSeconds(startOfDay(monday + 7, zone)),
  };
}

export async function weeklyXp(
  db: D1Database,
  userIds: string[],
  week: { from: number; to: number },
): Promise<Map<string, number>> {
  const rows = await db
    .prepare(
      `SELECT user_id, SUM(amount) AS total FROM xp_events
       WHERE user_id IN (SELECT value FROM json_each(?1)) AND at >= ?2 AND at < ?3
       GROUP BY user_id`,
    )
    .bind(JSON.stringify(userIds), week.from, week.to)
    .all<{ user_id: string; total: number }>();
  return new Map(rows.results.map((row) => [row.user_id, row.total]));
}

export async function getBoard({
  env,
  userId,
  now,
}: ApiContext): Promise<Response> {
  const db = env.DB;
  const friends = await db
    .prepare("SELECT id, friend_id FROM friendships WHERE user_id = ?1")
    .bind(userId)
    .all<{ id: number; friend_id: string }>();
  const week = await weekOf(db, userId, now);
  const totals = await weeklyXp(
    db,
    [userId, ...friends.results.map((row) => row.friend_id)],
    week,
  );
  const entries = [
    { you: true, id: null as number | null, xp: totals.get(userId) ?? 0 },
    ...friends.results.map((row) => ({
      you: false,
      id: row.id,
      xp: totals.get(row.friend_id) ?? 0,
    })),
  ]
    // On a tie the user comes first, then friends in the order they were made.
    .toSorted(
      (a, b) => b.xp - a.xp || Number(b.you) - Number(a.you) || a.id! - b.id!,
    )
    .map((entry, _, all) => ({
      rank: 1 + all.filter((other) => other.xp > entry.xp).length,
      you: entry.you,
      id: entry.id,
      xp: entry.xp,
    }));
  return reply({ weekStart: week.weekStart, entries });
}
