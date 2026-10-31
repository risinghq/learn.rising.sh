import { buildPushPayload } from "@block65/webcrypto-web-push";

import { DAY_MS, unixSeconds } from "./account.ts";
import { type ApiContext, fail, isRecord, readJson, reply } from "./http.ts";
import type { Env } from "./limits.ts";
import { logFailure } from "./log.ts";
import { type StreakRow, streakOf } from "./streak.ts";
import { localDay, localHour } from "./zone.ts";

const MAX_BODY_BYTES = 2000;
const MAX_ENDPOINT_CHARS = 600;
const MAX_SUBSCRIPTIONS = 5;
const KEY = /^[A-Za-z0-9_-]{1,200}={0,2}$/;

export const REMINDER_HOUR = 19;

const SEND_TIMEOUT_MS = 5000;
const SEND_BATCH = 20;

interface Vapid {
  publicKey: string;
  privateKey: string;
  subject: string;
}

// Reads the key pair and the contact from the secrets, or null when the
// deployment has none.
function vapidOf(env: Env): Vapid | null {
  const { VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_SUBJECT } = env;
  return VAPID_PUBLIC_KEY && VAPID_PRIVATE_KEY && VAPID_SUBJECT
    ? {
        publicKey: VAPID_PUBLIC_KEY,
        privateKey: VAPID_PRIVATE_KEY,
        subject: VAPID_SUBJECT,
      }
    : null;
}

// A push service is one of the hosts the deployment lists, or a subdomain of
// one. Without this a learner could make the Worker post to any address.
function allowed(endpoint: URL, hosts: string): boolean {
  return hosts
    .split(",")
    .map((host) => host.trim())
    .filter(Boolean)
    .some(
      (host) =>
        endpoint.hostname === host || endpoint.hostname.endsWith(`.${host}`),
    );
}

export async function getPushKey({ env }: ApiContext): Promise<Response> {
  const vapid = vapidOf(env);
  if (!vapid)
    return fail(503, "push_unavailable", "Los recordatorios no están activos.");
  return reply({ key: vapid.publicKey, hour: REMINDER_HOUR });
}

export async function postPush({
  request,
  env,
  userId,
  now,
}: ApiContext): Promise<Response> {
  if (!vapidOf(env))
    return fail(503, "push_unavailable", "Los recordatorios no están activos.");
  const body = await readJson(request, MAX_BODY_BYTES);
  if (body instanceof Response) return body;
  const keys = isRecord(body) && isRecord(body.keys) ? body.keys : undefined;
  const unknown =
    !isRecord(body) ||
    Object.keys(body).some((field) => !["endpoint", "keys"].includes(field)) ||
    !keys ||
    Object.keys(keys).some((field) => !["p256dh", "auth"].includes(field));
  if (
    unknown ||
    typeof body.endpoint !== "string" ||
    body.endpoint.length > MAX_ENDPOINT_CHARS ||
    typeof keys.p256dh !== "string" ||
    typeof keys.auth !== "string" ||
    !KEY.test(keys.p256dh) ||
    !KEY.test(keys.auth)
  )
    return fail(
      400,
      "bad_request",
      "La suscripción no tiene el formato correcto.",
    );
  let endpoint: URL;
  try {
    endpoint = new URL(body.endpoint);
  } catch {
    return fail(400, "bad_request", "El endpoint no es una dirección válida.");
  }
  if (endpoint.protocol !== "https:" || !allowed(endpoint, env.PUSH_HOSTS))
    return fail(400, "bad_endpoint", "Ese servicio de avisos no se admite.");

  // The count and the write are one statement, so racing requests cannot pass
  // the cap. A browser that already belongs to the user does not count.
  const saved = await env.DB.prepare(
    `INSERT INTO push_subscriptions (endpoint, user_id, p256dh, auth, created_at)
     SELECT ?1, ?2, ?3, ?4, ?5
     WHERE (
       SELECT COUNT(*) FROM push_subscriptions
       WHERE user_id = ?2 AND endpoint <> ?1
     ) < ?6
     ON CONFLICT (endpoint) DO UPDATE SET
       user_id = excluded.user_id, p256dh = excluded.p256dh, auth = excluded.auth`,
  )
    .bind(
      endpoint.href,
      userId,
      keys.p256dh,
      keys.auth,
      unixSeconds(now),
      MAX_SUBSCRIPTIONS,
    )
    .run();
  if (saved.meta.changes === 0)
    return fail(
      429,
      "too_many_browsers",
      "Ya hay varios navegadores con recordatorios. Desactiva alguno.",
    );
  return new Response(null, { status: 204 });
}

export async function deletePush({
  request,
  env,
  userId,
}: ApiContext): Promise<Response> {
  const body = await readJson(request, MAX_BODY_BYTES);
  if (body instanceof Response) return body;
  if (!isRecord(body) || typeof body.endpoint !== "string")
    return fail(400, "bad_request", "Falta el campo endpoint.");
  await env.DB.prepare(
    "DELETE FROM push_subscriptions WHERE endpoint = ?1 AND user_id = ?2",
  )
    .bind(body.endpoint, userId)
    .run();
  return new Response(null, { status: 204 });
}

export interface Reminder {
  userId: string;
  // The learner's current streak, which a missed day ends.
  streak: number;
  // The learner's local day, so one reminder goes out per day.
  day: number;
}

// Learners to remind at `now`: the local time is REMINDER_HOUR, the streak is
// alive, today has no XP, a browser accepted reminders and none went out today.
// The local day and hour need the learner's zone, which SQL cannot read, so SQL
// narrows to the streaks that can still be alive anywhere and the zone decides.
export async function dueReminders(
  db: D1Database,
  now: number,
): Promise<Reminder[]> {
  // A streak survives at most two freezes and the open day, and a local day is
  // at most one off the UTC day.
  const oldest = Math.floor(now / DAY_MS) - 4;
  const rows = await db
    .prepare(
      `SELECT u.id, u.time_zone, u.reminded_day,
              s.run, s.longest, s.freezes, s.last_day
       FROM users u JOIN streaks s ON s.user_id = u.id
       WHERE s.last_day >= ?1
         AND EXISTS (SELECT 1 FROM push_subscriptions p WHERE p.user_id = u.id)`,
    )
    .bind(oldest)
    .all<StreakRow & { id: string; time_zone: string; reminded_day: number }>();
  const due: Reminder[] = [];
  for (const row of rows.results) {
    if (localHour(now, row.time_zone) !== REMINDER_HOUR) continue;
    const day = localDay(now, row.time_zone);
    if (row.reminded_day >= day) continue;
    const streak = streakOf(row, day);
    if (streak.today || streak.current === 0) continue;
    due.push({ userId: row.id, streak: streak.current, day });
  }
  return due;
}

const days = (n: number) => `${n} ${n === 1 ? "día" : "días"}`;

async function deliver(
  vapid: Vapid,
  endpoint: string,
  keys: { p256dh: string; auth: string },
  reminder: Reminder,
): Promise<number> {
  const request = await buildPushPayload(
    {
      data: {
        title: `Tu racha de ${days(reminder.streak)} está en juego`,
        body: "Practica un poco hoy para mantenerla.",
        url: "/",
      },
      // The reminder is useless after the day ends.
      options: { ttl: 6 * 3600, urgency: "normal", topic: "racha" },
    },
    { endpoint, expirationTime: null, keys },
    vapid,
  );
  const response = await fetch(endpoint, {
    ...request,
    signal: AbortSignal.timeout(SEND_TIMEOUT_MS),
  });
  // The service does not read the body.
  void response.body?.cancel();
  return response.status;
}

interface Browser {
  endpoint: string;
  p256dh: string;
  auth: string;
}

// Sends one reminder to a browser and returns whether it took it. A browser the
// push service answers 404 or 410 for is forgotten.
async function sendTo(
  db: D1Database,
  vapid: Vapid,
  browser: Browser,
  reminder: Reminder,
): Promise<boolean> {
  try {
    const status = await deliver(vapid, browser.endpoint, browser, reminder);
    if (status === 404 || status === 410)
      await db
        .prepare("DELETE FROM push_subscriptions WHERE endpoint = ?1")
        .bind(browser.endpoint)
        .run();
    return status >= 200 && status < 300;
  } catch (error) {
    logFailure(error, "push");
    return false;
  }
}

async function remind(
  db: D1Database,
  vapid: Vapid,
  reminder: Reminder,
): Promise<number> {
  // The claim is one statement, so a repeated run sends nothing twice.
  const claimed = await db
    .prepare(
      `UPDATE users SET reminded_day = ?2
       WHERE id = ?1 AND reminded_day < ?2`,
    )
    .bind(reminder.userId, reminder.day)
    .run();
  if (claimed.meta.changes === 0) return 0;
  const browsers = await db
    .prepare(
      "SELECT endpoint, p256dh, auth FROM push_subscriptions WHERE user_id = ?1",
    )
    .bind(reminder.userId)
    .all<Browser>();
  const took = await Promise.all(
    browsers.results.map((browser) => sendTo(db, vapid, browser, reminder)),
  );
  return took.filter(Boolean).length;
}

// Sends the reminders due at `now` and returns how many browsers took one.
export async function sendReminders(env: Env, now: number): Promise<number> {
  const vapid = vapidOf(env);
  if (!vapid) return 0;
  const due = await dueReminders(env.DB, now);
  let sent = 0;
  for (let k = 0; k < due.length; k += SEND_BATCH) {
    // oxlint-disable-next-line eslint/no-await-in-loop -- A batch ends before the next starts, which bounds the open requests.
    const counts = await Promise.all(
      due
        .slice(k, k + SEND_BATCH)
        .map((reminder) => remind(env.DB, vapid, reminder)),
    );
    sent += counts.reduce((total, count) => total + count, 0);
  }
  return sent;
}
