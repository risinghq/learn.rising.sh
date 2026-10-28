import { unixSeconds } from "./account.ts";
import { EXERCISE } from "./contract.ts";

// What the Worker records about a run. It comes from the container's JSON, which
// grades the code: the page cannot fake a result. It never carries the code,
// `stdout`, the error text or the `message` of a case, which may repeat what the
// learner wrote.
export interface Attempt {
  exercise: string;
  mode: "run" | "check";
  outcome: "pass" | "fail" | "error" | "timeout";
  failed: string[];
  errorKind: string | null;
  hints: number;
  ms: number;
  codeBytes: number;
}

const MAX_FAILED = 50;
const MAX_CASE_CHARS = 120;
const KILLED = new Set(["time", "memory", "disk", "output", "scan"]);
// The name of a Python exception; any other error text is "other".
const EXCEPTION = /^([A-Za-z]{1,40}(?:Error|Exception))\b/;

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

// `request` is what the page sent (only `mode` and `exercise` are used) and `result`
// the body the container replied with. Returns null if there is nothing to record.
export function toAttempt(
  request: { mode?: unknown; exercise?: unknown },
  codeBytes: number,
  hintsHeader: string | null,
  result: unknown,
): Attempt | null {
  const { mode, exercise } = request;
  if (mode !== "run" && mode !== "check") return null;
  if (typeof exercise !== "string" || !EXERCISE.test(exercise)) return null;
  if (!isRecord(result) || typeof result.passed !== "boolean") return null;

  const killed =
    typeof result.killed === "string" && KILLED.has(result.killed)
      ? result.killed
      : null;
  let outcome: Attempt["outcome"] = result.passed ? "pass" : "fail";
  let errorKind: string | null = null;
  if (killed === "time") {
    outcome = "timeout";
  } else if (killed) {
    outcome = "error";
    errorKind = `killed_${killed}`;
  } else if (typeof result.error === "string") {
    outcome = "error";
    errorKind = EXCEPTION.exec(result.error)?.[1] ?? "other";
  }

  const failed = Array.isArray(result.tests)
    ? result.tests
        .filter(
          (test) =>
            isRecord(test) &&
            test.passed === false &&
            typeof test.name === "string",
        )
        .slice(0, MAX_FAILED)
        .map((test) => (test.name as string).slice(0, MAX_CASE_CHARS))
    : [];
  const hints = /^[0-9]$/.test(hintsHeader ?? "") ? Number(hintsHeader) : 0;
  const ms =
    typeof result.ms === "number" && Number.isFinite(result.ms)
      ? Math.max(0, Math.round(result.ms))
      : 0;
  return { exercise, mode, outcome, failed, errorKind, hints, ms, codeBytes };
}

export async function recordAttempt(
  db: D1Database,
  userId: string | null,
  attempt: Attempt,
  now: number,
): Promise<void> {
  const statements = [
    db
      .prepare(
        `INSERT INTO attempts (at, user_id, exercise, mode, outcome, failed, error_kind, hints, ms, code_bytes)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)`,
      )
      .bind(
        unixSeconds(now),
        userId,
        attempt.exercise,
        attempt.mode,
        attempt.outcome,
        JSON.stringify(attempt.failed),
        attempt.errorKind,
        attempt.hints,
        attempt.ms,
        attempt.codeBytes,
      ),
  ];
  // Only a passing check for an authenticated user sets `exercise_state.passed`.
  // The pass survives attempt retention, while `updated_at = 0` lets page edits win.
  if (userId && attempt.mode === "check" && attempt.outcome === "pass") {
    statements.push(
      db
        .prepare(
          `INSERT INTO exercise_state (user_id, exercise, passed, updated_at)
           VALUES (?1, ?2, 1, 0)
           ON CONFLICT (user_id, exercise) DO UPDATE SET passed = 1`,
        )
        .bind(userId, attempt.exercise),
    );
  }
  await db.batch(statements);
}
