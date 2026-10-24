import { DurableObject } from "cloudflare:workers";

import { type Rates, nanoFor } from "./container.ts";

export type Verdict =
  | { ok: true }
  | { ok: false; scope: "minute" | "day"; retryAfter: number };

const MINUTE_MS = 60_000;

// Un objeto por IP y día, nombrado con un HMAC de la IP en index.ts. Borra su
// estado cuando termina el día.
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

// Topes de gasto en nanodólares. `total` vale para todos; `public` y `day` solo
// para quien no es mantenedor, y `day` cuenta únicamente el gasto público de
// un día UTC.
export interface Caps {
  total: number;
  public: number;
  day: number;
}

export type Who = "public" | "maintainer";

// Lo que una ejecución aparta en una instancia. Es el recibo que `settle`
// devuelve ajustado, y no lleva nada de quien la pidió.
export interface Hold {
  id: string;
  month: string;
  day: string;
  who: Who;
  instance: string;
  // Lo apartado, y la parte de ello que paga la memoria y el disco encendidos.
  nano: number;
  idleNano: number;
  // La ventana de encendido que esta reserva añadió: de `from` a `until`.
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
  // La reserva que fijó `until`. Solo ella puede acortarlo al terminar.
  owner: string;
}

const isoMonth = (ms: number) => new Date(ms).toISOString().slice(0, 7);
const isoDay = (ms: number) => new Date(ms).toISOString().slice(0, 10);

// Guarda el gasto estimado del mes y del día en nanodólares, y el instante en que
// se espera que se apague cada instancia. Descarta los meses y días anteriores.
// El gasto de una ejecución es su tiempo de CPU más el tiempo que su instancia
// pasa encendida por su causa: desde el fin de lo que ya estaba cobrado hasta
// `sleepAfter` después de que acaba.
//
// El objeto atiende una llamada a la vez, y `reserve` y `settle` no esperan nada
// salvo su propio almacenamiento, así que comprobar y apartar es una sola
// operación.
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

  // Devuelve `nano` solo si el periodo sigue siendo el de la reserva.
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

  // Aparta lo que costaría, como mucho, una ejecución de `runMs` en `instance` si
  // cabe, y dice cuál tope lo impide si no.
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

  // Cambia lo apartado por el coste medido, que nunca pasa de lo apartado. Sin
  // `ran` se devuelve todo. El tiempo encendido solo se acorta si nadie lo
  // alargó después, porque quien lo alargó cobró desde el fin de esta ventana.
  // Si el mes o el día ya cambió, no hay nada que ajustar.
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
