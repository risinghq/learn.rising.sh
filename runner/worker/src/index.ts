import { Container } from "@cloudflare/containers";

import { isMaintainer, sessionUser } from "./account.ts";
import { handleApi } from "./api.ts";
import { recordAttempt, toAttempt } from "./attempts.ts";
import { handleAuth } from "./auth.ts";
import { type Rates, SLEEP_AFTER_SECONDS } from "./container.ts";
import { fail } from "./http.ts";
import { ConfigError, type Env, type Limits, loadLimits } from "./limits.ts";
import { type Entry, logFailure, logRun } from "./log.ts";
import {
  Budget,
  type Hold,
  RateLimiter,
  type Verdict,
  type Who,
} from "./meters.ts";
import { purge } from "./purge.ts";
import { hasSession, issueSession, verifyTurnstile } from "./session.ts";
import { take } from "./throttle.ts";

export { Budget, RateLimiter };

// An instance serves one job at a time (runner/server.py). The Worker spreads
// runs among `INSTANCES` and retries once on the next one when the chosen one
// answers 503.
export class Runner extends Container {
  defaultPort = 8080;
  sleepAfter = `${SLEEP_AFTER_SECONDS}s`;
  enableInternet = false;
}

const instanceName = (index: number) => `instance-${index}`;

interface Exports {
  Runner: DurableObjectNamespace<Runner>;
  RateLimiter: DurableObjectNamespace<RateLimiter>;
  Budget: DurableObjectNamespace<Budget>;
}

class Refusal extends Error {
  constructor(
    readonly entry: Entry,
    readonly reason: string,
    readonly message: string,
    readonly headers: Record<string, string> = {},
    readonly extra: Record<string, string> = {},
  ) {
    super(message);
  }
}

function refuse(response: Refusal): Response {
  return Response.json(
    { error: response.message, reason: response.reason, ...response.extra },
    {
      status: response.entry.status,
      headers: { "Cache-Control": "no-store", ...response.headers },
    },
  );
}

const utf8Length = (text: string) => new TextEncoder().encode(text).length;

function throwIfLimited(verdict: Verdict): void {
  if (verdict.ok) return;
  const day = verdict.scope === "day";
  throw new Refusal(
    { outcome: day ? "rate_day" : "rate_minute", status: 429 },
    day ? "rate_day" : "rate_minute",
    day
      ? `Llegaste al límite de ejecuciones de hoy. Puedes volver a ejecutar en ${wait(verdict.retryAfter)}.`
      : `Estás ejecutando demasiado seguido. Espera ${wait(verdict.retryAfter)} y vuelve a intentarlo.`,
    { "Retry-After": String(verdict.retryAfter) },
  );
}

function wait(seconds: number): string {
  if (seconds < 90) return `${seconds} s`;
  if (seconds < 5400) return `${Math.ceil(seconds / 60)} min`;
  return `${Math.ceil(seconds / 3600)} h`;
}

async function readBody(request: Request, limits: Limits): Promise<Uint8Array> {
  const tooLarge = () =>
    new Refusal(
      { outcome: "too_large", status: 413 },
      "too_large",
      `La petición es demasiado grande: el código no puede pasar de ${limits.maxCodeBytes} bytes.`,
    );
  const declared = Number(request.headers.get("content-length"));
  if (declared > limits.maxBodyBytes) throw tooLarge();
  const chunks: Uint8Array[] = [];
  let total = 0;
  if (request.body) {
    const reader = request.body.getReader();
    for (;;) {
      // oxlint-disable-next-line eslint/no-await-in-loop -- The chunks of a stream are read in order.
      const { done, value } = await reader.read();
      if (done) break;
      total += value.length;
      if (total > limits.maxBodyBytes) {
        // oxlint-disable-next-line eslint/no-await-in-loop -- It is cancelled once and the loop ends.
        await reader.cancel();
        throw tooLarge();
      }
      chunks.push(value);
    }
  }
  const body = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.length;
  }
  return body;
}

// Swaps the reservation for the measured cost and returns what was charged. A failure is
// logged and not propagated: an unadjusted reservation counts too much, never too little,
// and must not hide the error the request already carried.
async function settle(
  budget: DurableObjectStub<Budget>,
  rates: Rates,
  hold: Hold,
  ran?: { busyMs: number; endedAt: number },
): Promise<number> {
  try {
    return await budget.settle(hold, rates, ran);
  } catch (error) {
    logFailure(error, "settle");
    return hold.nano;
  }
}

// A reservation of this request on an instance, and when the work was sent to it.
interface Attempt {
  hold: Hold;
  reservedAt: number;
  sentAt?: number;
  endedAt?: number;
  settled?: boolean;
}

const MARIMO = "Los cuadernos de marimo siguen funcionando en tu equipo.";

// `entry` is the request's: it is completed with the time and the cost before it
// is logged, also when the cap is hit on the retry.
function overBudget(
  entry: Entry,
  reason: "budget" | "budget_day",
  now: number,
): Refusal {
  const at = new Date(now);
  entry.outcome = reason;
  entry.status = 503;
  if (reason === "budget_day") {
    const retryAfter = Math.ceil(
      (Date.UTC(at.getUTCFullYear(), at.getUTCMonth(), at.getUTCDate() + 1) -
        now) /
        1000,
    );
    return new Refusal(
      entry,
      reason,
      `El corredor alcanzó su presupuesto de hoy y no ejecuta más código hasta mañana. Puedes volver a ejecutar en ${wait(retryAfter)}. ${MARIMO}`,
      { "Retry-After": String(retryAfter) },
    );
  }
  const retryAfter = Math.ceil(
    (Date.UTC(at.getUTCFullYear(), at.getUTCMonth() + 1, 1) - now) / 1000,
  );
  return new Refusal(
    entry,
    reason,
    `El corredor alcanzó su presupuesto de este mes y no ejecuta más código hasta que empiece el siguiente. ${MARIMO}`,
    { "Retry-After": String(retryAfter) },
  );
}

async function run(
  request: Request,
  env: Env,
  exports: Exports,
): Promise<Response> {
  const limits = loadLimits(env);
  const now = Date.now();
  const ip = request.headers.get("cf-connecting-ip") ?? "";
  const entry: Entry = { outcome: "ok", status: 0 };
  const budget = exports.Budget.get(exports.Budget.idFromName("budget"));
  // The request's reservations. One stays open until it is adjusted.
  const attempts: Attempt[] = [];
  // Adjusts the open reservations to the measured cost and returns what was charged.
  // One that was sent no work returns everything.
  const close = async (): Promise<number> => {
    const end = Date.now();
    const costs = await Promise.all(
      attempts
        .filter((attempt) => !attempt.settled)
        .map((attempt) => {
          attempt.settled = true;
          const endedAt = attempt.endedAt ?? end;
          return settle(
            budget,
            limits.rates,
            attempt.hold,
            attempt.sentAt === undefined
              ? undefined
              : { busyMs: endedAt - attempt.sentAt, endedAt },
          );
        }),
    );
    return costs.reduce((sum, cost) => sum + cost, 0);
  };

  try {
    const userId = await sessionUser(
      env.DB,
      request.headers.get("cookie"),
      now,
    );
    const maintainer =
      userId !== null &&
      (await isMaintainer(env.DB, userId, limits.maintainers));
    const who: Who = maintainer ? "maintainer" : "public";
    // A signed-in user shares the IP with their class: their per-IP cap is higher and
    // what bounds them is their own cap.
    const ipFactor = userId ? limits.signedInIpFactor : 1;
    const secret = env.TURNSTILE_SECRET;
    throwIfLimited(
      await take(
        exports.RateLimiter,
        secret,
        "limiter",
        ip,
        now,
        limits.perMinute * ipFactor,
        limits.perDay * ipFactor,
      ),
    );
    // A maintainer has no daily cap of their own: the budget bounds them.
    if (userId && !maintainer) {
      throwIfLimited(
        await take(
          exports.RateLimiter,
          secret,
          "user",
          userId,
          now,
          limits.perMinute,
          limits.perDay,
        ),
      );
    }

    const body = await readBody(request, limits);
    let parsed: { code?: unknown; mode?: unknown; exercise?: unknown };
    try {
      parsed = JSON.parse(new TextDecoder().decode(body));
    } catch {
      throw new Refusal(
        { outcome: "bad_request", status: 400 },
        "bad_request",
        "La petición no es un JSON válido.",
      );
    }
    if (
      parsed === null ||
      typeof parsed !== "object" ||
      typeof parsed.code !== "string"
    ) {
      throw new Refusal(
        { outcome: "bad_request", status: 400 },
        "bad_request",
        "Falta el campo code.",
      );
    }
    entry.mode = parsed.mode;
    entry.exercise = parsed.exercise;
    entry.codeBytes = utf8Length(parsed.code);
    if (entry.codeBytes > limits.maxCodeBytes) {
      throw new Refusal(
        { ...entry, outcome: "too_large", status: 413 },
        "too_large",
        `El código ocupa ${entry.codeBytes} bytes y el máximo son ${limits.maxCodeBytes}.`,
      );
    }

    // Sets aside what the run would cost on that instance: its CPU and the time
    // it keeps the instance on. It goes before Turnstile so as not to spend a
    // verification when there is no budget left.
    const reserve = async (index: number): Promise<Attempt> => {
      const reservedAt = Date.now();
      const reserved = await budget.reserve({
        who,
        instance: instanceName(index),
        now: reservedAt,
        runMs: limits.reserveMs,
        rates: limits.rates,
        caps: limits.caps,
      });
      if (!reserved.ok) throw overBudget(entry, reserved.reason, reservedAt);
      const attempt: Attempt = { hold: reserved.hold, reservedAt };
      attempts.push(attempt);
      return attempt;
    };
    const firstIndex = Math.floor(Math.random() * limits.instances);
    const first = await reserve(firstIndex);

    let cookie: string | undefined;
    // A maintainer signs in with GitHub and skips Turnstile. Everyone else,
    // signed in or not, passes it once per session.
    if (
      !maintainer &&
      !(await hasSession(
        env.TURNSTILE_SECRET,
        ip,
        now,
        request.headers.get("cookie"),
      ))
    ) {
      const token = request.headers.get("x-turnstile-token");
      if (!token) {
        if (!env.TURNSTILE_SITE_KEY)
          throw new ConfigError("TURNSTILE_SITE_KEY must be defined");
        throw new Refusal(
          { ...entry, outcome: "turnstile_missing", status: 403 },
          "turnstile_missing",
          "Antes de ejecutar código hay que comprobar que eres una persona.",
          {},
          { sitekey: env.TURNSTILE_SITE_KEY },
        );
      }
      const verification = await verifyTurnstile(env.TURNSTILE_SECRET, token);
      if (verification === "unavailable") {
        throw new Refusal(
          { ...entry, outcome: "turnstile_unavailable", status: 503 },
          "turnstile_unavailable",
          "No se pudo comprobar que eres una persona. Vuelve a intentarlo en unos segundos.",
          { "Retry-After": "10" },
        );
      }
      if (verification === "rejected") {
        throw new Refusal(
          { ...entry, outcome: "turnstile_failed", status: 403 },
          "turnstile_failed",
          "No pasó la comprobación de que eres una persona. Recarga la página e inténtalo de nuevo.",
        );
      }
      cookie = await issueSession(
        env.TURNSTILE_SECRET,
        ip,
        now,
        limits.sessionMs,
      );
    }

    // The container receives only the body and its type. It does not receive the cookie,
    // the IP or the Turnstile token.
    // The instance that has not answered this request yet. One that answers, 503
    // included, stops belonging to the request: the 503 says it is serving another
    // learner's job, and stopping it would kill that job.
    let pending = undefined as DurableObjectStub<Runner> | undefined;
    let stopped = false;
    const send = async (index: number, attempt: Attempt) => {
      const instance = exports.Runner.get(
        exports.Runner.idFromName(instanceName(index)),
      );
      // An instance chosen after the cap must never start.
      if (stopped) throw new Error("run stopped");
      pending = instance;
      attempt.sentAt = Date.now();
      try {
        const response = await instance.fetch(
          new Request(new URL("/run", request.url), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body,
          }),
        );
        pending = undefined;
        return response;
      } finally {
        attempt.endedAt ??= Date.now();
      }
    };
    const started = Date.now();
    let result: Response | undefined;
    // The run, with its retry, has RESERVED_BUSY_SECONDS from when it was set
    // aside, and Turnstile has already used part of that time. Past that cap, the
    // reservation would not cover the time the instance would stay on.
    let timer: ReturnType<typeof setTimeout> | undefined;
    const ceiling = new Promise<undefined>((resolve) => {
      timer = setTimeout(
        () => resolve(undefined),
        Math.max(0, limits.reserveMs - (started - first.reservedAt)),
      );
    });
    const work = (async () => {
      const response = await send(firstIndex, first);
      if (response.status !== 503) return response;
      // That instance is serving another learner: try the next one.
      const next = (firstIndex + 1) % limits.instances;
      if (stopped) throw new Error("run stopped");
      const retry = await reserve(next);
      // The cap may have hit while setting aside: nobody will adjust this reservation.
      if (stopped) {
        await close();
        throw new Error("run stopped");
      }
      return send(next, retry);
    })();
    // If the cap wins, the late rejection of `work` has nobody to reach.
    work.catch(() => {});
    try {
      result = await Promise.race([work, ceiling]);
      if (!result) {
        stopped = true;
        await pending?.destroy().catch((error) => logFailure(error, "stop"));
      }
    } finally {
      clearTimeout(timer);
      entry.busyMs = Date.now() - started;
      // If recording the cost fails, the reservation stays and the container's
      // error, if there was one, carries on.
      entry.costNano = await close();
    }
    if (!result) {
      throw new Refusal(
        { ...entry, outcome: "run_too_long", status: 504 },
        "run_too_long",
        "La ejecución tardó más de lo que el corredor permite y se detuvo. Revisa si el código tiene un bucle sin fin.",
      );
    }
    entry.status = result.status;
    logRun(entry);
    const headers = new Headers({
      "Content-Type": result.headers.get("content-type") ?? "application/json",
      "Cache-Control": "no-store",
    });
    if (cookie) headers.set("Set-Cookie", cookie);
    const text = await result.text();
    if (result.status === 200) {
      // Recording the attempt must not take the learner's result away.
      try {
        const attempt = toAttempt(
          parsed,
          entry.codeBytes ?? 0,
          request.headers.get("x-hints"),
          JSON.parse(text),
        );
        if (attempt) await recordAttempt(env.DB, userId, attempt, now);
      } catch (error) {
        logFailure(error, "attempt");
      }
    }
    return new Response(text, { status: result.status, headers });
  } catch (error) {
    await close();
    if (error instanceof Refusal) {
      logRun(error.entry);
      return refuse(error);
    }
    throw error;
  }
}

export default {
  async fetch(
    request: Request,
    env: Env,
    ctx: ExecutionContext,
  ): Promise<Response> {
    const { pathname } = new URL(request.url);
    // Answering here avoids starting a container for an unlimited request.
    if (pathname === "/health") return Response.json({ ok: true });
    const account = pathname.startsWith("/auth/")
      ? "auth"
      : pathname.startsWith("/api/")
        ? "api"
        : null;
    if (account) {
      const { RateLimiter: limiters } = (ctx as unknown as { exports: Exports })
        .exports;
      try {
        const limits = loadLimits(env);
        const handle = account === "auth" ? handleAuth : handleApi;
        return await handle(request, env, limits, limiters, Date.now());
      } catch (error) {
        logFailure(error, account);
        return fail(500, "internal_error", "Error interno.");
      }
    }
    // The routes that are not the platform's are served from site/.
    if (pathname !== "/run") return env.ASSETS.fetch(request);
    if (request.method !== "POST") {
      return Response.json(
        { error: "usa POST" },
        { status: 405, headers: { Allow: "POST" } },
      );
    }
    try {
      return await run(
        request,
        env,
        (ctx as unknown as { exports: Exports }).exports,
      );
    } catch (error) {
      logFailure(error);
      return Response.json(
        { error: "Error interno del corredor.", reason: "internal_error" },
        { status: 500 },
      );
    }
  },

  // The daily cron of cloudflare.config.ts.
  async scheduled(controller: ScheduledController, env: Env): Promise<void> {
    try {
      await purge(env.DB, loadLimits(env), controller.scheduledTime);
    } catch (error) {
      logFailure(error, "purge");
      throw error;
    }
  },
};
