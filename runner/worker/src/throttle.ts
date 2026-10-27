import type { RateLimiter, Verdict } from "./meters.ts";
import { mac } from "./session.ts";

const DAY_MS = 86_400_000;

// Count a request in the counter of `key` under `label`. The object name is an
// HMAC of the day and the key (an IP or a user), so it cannot be traced back to
// them without the secret. Labels keep the counters of one key apart.
export async function take(
  limiters: DurableObjectNamespace<RateLimiter>,
  secret: string,
  label: string,
  key: string,
  now: number,
  perMinute: number,
  perDay: number,
): Promise<Verdict> {
  const dayStart = Math.floor(now / DAY_MS) * DAY_MS;
  const name = await mac(secret, label, `${dayStart}|${key}`);
  const limiter = limiters.get(limiters.idFromName(name));
  return limiter.take(now, perMinute, perDay, dayStart + DAY_MS);
}
