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

// One line per request with fixed fields. It never receives the code, the IP, the
// token, the cookie or the text of an error: `mode` and `exercise` are copied only if
// they have the shape of a contract value, and the rest are numbers and a name.
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

export type Where =
  | "settle"
  | "stop"
  | "attempt"
  | "auth"
  | "api"
  | "purge"
  | "push";

// `where` names the step that failed when the request carries on. `auth`,
// `api`, `purge` and `push` are not steps of /run: they are their own event.
export function logFailure(error: unknown, where?: Where): void {
  const own =
    where === "auth" ||
    where === "api" ||
    where === "purge" ||
    where === "push";
  console.error(
    JSON.stringify({
      event: own ? where : "run",
      outcome: "internal_error",
      status: where && !own ? undefined : 500,
      where: own ? undefined : where,
      error: error instanceof Error ? error.name : "unknown",
      // Only a configuration error carries text: it names a variable, not data.
      detail: error instanceof ConfigError ? error.message : undefined,
    }),
  );
}
