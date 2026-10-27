import { DAY_MS, unixSeconds } from "./account.ts";
import type { Limits } from "./limits.ts";

// The daily purge (cron). Attempts and accounts with no visits are deleted once
// their period passes; a deleted account takes its progress and attempts with it
// through the foreign keys.
export async function purge(
  db: D1Database,
  limits: Limits,
  now: number,
): Promise<void> {
  await db.batch([
    db
      .prepare("DELETE FROM attempts WHERE at < ?1")
      .bind(unixSeconds(now - limits.attemptRetentionMs)),
    db
      .prepare("DELETE FROM sessions WHERE expires_at < ?1")
      .bind(unixSeconds(now)),
    db
      .prepare("DELETE FROM users WHERE seen_day < ?1")
      .bind(Math.floor((now - limits.accountRetentionMs) / DAY_MS)),
  ]);
}
