import { DurableObject } from "cloudflare:workers";

import { type Rates, nanoFor } from "./container.ts";

export type Verdict =
  | { ok: true }
  | { ok: false; scope: "minute" | "day"; retryAfter: number };

const MINUTE_MS = 60_000;

// One object per IP and day, named with an HMAC of the IP in index.ts. It deletes
// its state when the day ends.
export class RateLimiter extends DurableObject {
  async take(
    now: number,
    perMinute: number,
    perDay: number,
    dayEnd: number,
  ): Promise<Verdict> {
    const stored = await this.ctx.storage.get<{
      minute: number;
      inMinute: number;
      inDay: number;
    }>("count");
    const minute = Math.floor(now / MINUTE_MS);
    const count = {
      minute,
      inMinute: stored?.minute === minute ? stored.inMinute : 0,
      inDay: stored?.inDay ?? 0,
    };
    if (count.inDay >= perDay) {
      return {
        ok: false,
        scope: "day",
        retryAfter: Math.max(1, Math.ceil((dayEnd - now) / 1000)),
      };
    }
    if (count.inMinute >= perMinute) {
      const next = (minute + 1) * MINUTE_MS;
      return {
        ok: false,
        scope: "minute",
        retryAfter: Math.max(1, Math.ceil((next - now) / 1000)),
      };
    }
    count.inMinute += 1;
    count.inDay += 1;
    await this.ctx.storage.put("count", count);
    await this.ctx.storage.setAlarm(dayEnd + MINUTE_MS);
    return { ok: true };
  }

  async alarm(): Promise<void> {
    await this.ctx.storage.deleteAll();
  }
}

// Spending caps in nanodollars. `total` applies to everyone; `public` and `day`
// only to those who are not maintainers, and `day` counts only the public spend
// of one UTC day.
export interface Caps {
  total: number;
  public: number;
  day: number;
}

export type Who = "public" | "maintainer";

// What a run sets aside on an instance. It is the receipt that `settle`
// returns adjusted, and it carries nothing about who asked for the run.
export interface Hold {
  id: string;
  month: string;
  day: string;
  who: Who;
  instance: string;
  // What was set aside, and the part of it that pays for memory and disk while on.
  nano: number;
  idleNano: number;
  // The on-window that this reservation added: from `from` to `until`.
  from: number;
  until: number;
}

export type Reserved =
  | { ok: true; hold: Hold }
  | { ok: false; reason: "budget" | "budget_day" };

interface Spend {
  period: string;
  nano: number;
}

interface Awake {
  until: number;
  // The reservation that set `until`. Only it can shorten it when it ends.
  owner: string;
}

const isoMonth = (ms: number) => new Date(ms).toISOString().slice(0, 7);
const isoDay = (ms: number) => new Date(ms).toISOString().slice(0, 10);

// Stores the estimated spend of the month and the day in nanodollars, and the
// moment each instance is expected to shut down. It discards earlier months and days.
// The spend of a run is its CPU time plus the time its instance
// stays on because of it: from the end of what was already billed until
// `sleepAfter` after it finishes.
//
// The object serves one call at a time, and `reserve` and `settle` wait for nothing
// except their own storage, so checking and setting aside is a single
// operation.
export class Budget extends DurableObject {
  private async spent(key: "month" | "day", period: string): Promise<number> {
    const stored = await this.ctx.storage.get<Spend>(key);
    return stored?.period === period ? stored.nano : 0;
  }

  private async add(
    key: "month" | "day",
    period: string,
    nano: number,
  ): Promise<void> {
    const total = await this.spent(key, period);
    await this.ctx.storage.put(key, { period, nano: total + nano });
  }

  // Returns `nano` only if the period is still the one of the reservation.
  private async refund(
    key: "month" | "day",
    period: string,
    nano: number,
  ): Promise<void> {
    const stored = await this.ctx.storage.get<Spend>(key);
    if (stored?.period !== period) return;
    await this.ctx.storage.put(key, {
      period,
      nano: Math.max(0, stored.nano - nano),
    });
  }

  // Sets aside what a run of `runMs` on `instance` would cost at most, if it
  // fits, and says which cap prevents it if not.
  async reserve(request: {
    who: Who;
    instance: string;
    now: number;
    runMs: number;
    rates: Rates;
    caps: Caps;
  }): Promise<Reserved> {
    const { who, instance, now, runMs, rates, caps } = request;
    const month = isoMonth(now);
    const day = isoDay(now);
    const awake = await this.ctx.storage.get<Awake>(`awake:${instance}`);
    const from = Math.max(now, awake?.until ?? 0);
    const until = Math.max(from, now + runMs + rates.sleepMs);
    const idleNano = nanoFor(until - from, rates.idle);
    const nano = nanoFor(runMs, rates.cpu) + idleNano;

    const cap = who === "public" ? caps.public : caps.total;
    if ((await this.spent("month", month)) + nano > cap) {
      return { ok: false, reason: "budget" };
    }
    if (who === "public" && (await this.spent("day", day)) + nano > caps.day) {
      return { ok: false, reason: "budget_day" };
    }

    const id = crypto.randomUUID();
    await this.add("month", month, nano);
    if (who === "public") await this.add("day", day, nano);
    if (until > from) {
      await this.ctx.storage.put<Awake>(`awake:${instance}`, {
        until,
        owner: id,
      });
    }
    return {
      ok: true,
      hold: { id, month, day, who, instance, nano, idleNano, from, until },
    };
  }

  // Swaps what was set aside for the measured cost, which never exceeds what was set
  // aside. Without `ran` everything is returned. The on-time is shortened only if
  // nobody extended it afterwards, because whoever extended it was billed from the
  // end of this window. If the month or the day has changed, there is nothing to adjust.
  async settle(
    hold: Hold,
    rates: Rates,
    ran?: { busyMs: number; endedAt: number },
  ): Promise<number> {
    const key = `awake:${hold.instance}`;
    const awake = await this.ctx.storage.get<Awake>(key);
    let idleNano = hold.idleNano;
    if (awake?.owner === hold.id) {
      const asleep = ran
        ? Math.min(hold.until, Math.max(hold.from, ran.endedAt + rates.sleepMs))
        : hold.from;
      idleNano = nanoFor(asleep - hold.from, rates.idle);
      await this.ctx.storage.put<Awake>(key, {
        until: asleep,
        owner: hold.id,
      });
    }
    const actual = Math.min(
      hold.nano,
      (ran ? nanoFor(ran.busyMs, rates.cpu) : 0) + idleNano,
    );
    const back = hold.nano - actual;
    await this.refund("month", hold.month, back);
    if (hold.who === "public") await this.refund("day", hold.day, back);
    return actual;
  }
}
