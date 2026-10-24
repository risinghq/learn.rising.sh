import { EXERCISE } from "./contract.ts";
import { ConfigError } from "./limits.ts";

export type Outcome =
  | "ok"
  | "rate_minute"
  | "rate_day"
  | "bad_request"
  | "too_large"
  | "turnstile_missing"
  | "turnstile_failed"
  | "turnstile_unavailable"
  | "budget"
  | "budget_day"
  | "run_too_long"
  | "internal_error";

export interface Entry {
  outcome: Outcome;
  status: number;
  mode?: unknown;
  exercise?: unknown;
  codeBytes?: number;
  busyMs?: number;
  costNano?: number;
}

// Una línea por petición con campos fijos. Nunca recibe el código, la IP, el
// token, la cookie ni el texto de un error: `mode` y `exercise` se copian solo si
// tienen la forma de un valor del contrato, y lo demás son números y un nombre.
export function logRun(entry: Entry): void {
  console.log(
    JSON.stringify({
      event: "run",
      outcome: entry.outcome,
      status: entry.status,
      mode:
        entry.mode === "run" || entry.mode === "check" ? entry.mode : undefined,
      exercise:
        typeof entry.exercise === "string" && EXERCISE.test(entry.exercise)
          ? entry.exercise
          : undefined,
      code_bytes: entry.codeBytes,
      busy_ms: entry.busyMs,
      cost_nano_usd: entry.costNano,
    }),
  );
}

export type Where = "settle" | "stop" | "attempt" | "auth" | "api" | "purge";

// `where` nombra el paso que falló cuando la petición sigue su camino. `auth`,
// `api` y `purge` no son pasos de /run: son su propio evento.
export function logFailure(error: unknown, where?: Where): void {
  const own = where === "auth" || where === "api" || where === "purge";
  console.error(
    JSON.stringify({
      event: own ? where : "run",
      outcome: "internal_error",
      status: where && !own ? undefined : 500,
      where: own ? undefined : where,
      error: error instanceof Error ? error.name : "unknown",
      // Solo un error de configuración lleva texto: nombra una variable, no datos.
      detail: error instanceof ConfigError ? error.message : undefined,
    }),
  );
}
