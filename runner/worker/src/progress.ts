import { unixSeconds } from "./account.ts";
import { EXERCISE } from "./contract.ts";

// A learner's progress, in the shape the page sends and receives. The keys
// of `kv` are those of localStorage; `done` is `qiskit:done` and `exercises` are the
// `qiskit:exercise:<id>`. What is not here (preferences, `reflect`) never leaves the
// browser.
export interface ExerciseState {
  // Only a learner who allows it sends their code.
  code?: string | null;
  hints: number;
  checks: number;
  passed: boolean;
  // Unix milliseconds of the last edit: the most recent code wins.
  at: number;
}

export interface Progress {
  done: string[];
  exercises: Record<string, ExerciseState>;
  kv: Record<string, unknown>;
}

export const MAX_CODE_BYTES = 20_000;
const MAX_DONE = 500;
const MAX_EXERCISES = 100;
const MAX_KV_KEYS = 2000;
const MAX_KV_BYTES = 64_000;
const MAX_ITEMS = 1000;

export const LESSON = /^[a-z0-9][a-z0-9-]{0,59}$/;

const isInt = (value: unknown): value is number =>
  typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const list = (
  value: unknown,
  accepts: (item: unknown) => boolean,
): value is unknown[] =>
  Array.isArray(value) && value.length <= MAX_ITEMS && value.every(accepts);

// Each family of `kv` keys: the shape of its value and how the stored value and
// the incoming one are merged. Union and maximum do not depend on order, so two
// tabs that sync end in the same state.
interface Family {
  key: RegExp;
  valid(value: unknown): boolean;
  merge(stored: unknown, incoming: unknown): unknown;
}

const union = (stored: unknown, incoming: unknown) =>
  [...new Set([...(stored as unknown[]), ...(incoming as unknown[])])].toSorted(
    (a, b) =>
      typeof a === "number" && typeof b === "number"
        ? a - b
        : String(a).localeCompare(String(b)),
  );

const isBox = (value: unknown) =>
  isRecord(value) &&
  isInt(value.box) &&
  value.box <= 20 &&
  typeof value.due === "number" &&
  Number.isFinite(value.due);

const FAMILIES: Family[] = [
  {
    key: /^qiskit:heard:[a-z0-9-]{1,60}$/,
    valid: (value) => list(value, isInt),
    merge: union,
  },
  {
    key: /^qiskit:hitos$/,
    valid: (value) => list(value, isInt),
    merge: union,
  },
  {
    key: /^qiskit:misiones$/,
    valid: (value) =>
      list(
        value,
        (item) =>
          typeof item === "string" && /^[A-Za-z0-9_./-]{1,100}$/.test(item),
      ),
    merge: union,
  },
  {
    key: /^qiskit:pos:[a-z0-9-]{1,60}$/,
    valid: isInt,
    merge: (stored, incoming) => Math.max(stored as number, incoming as number),
  },
  {
    // A bet is not changed: the first one saved is the one that counts.
    key: /^qiskit:predict:[a-z0-9-]{1,60}:[A-Za-z0-9_-]{1,60}$/,
    valid: isInt,
    merge: (stored) => stored,
  },
  {
    key: /^qiskit:repaso$/,
    valid: (value) =>
      isRecord(value) &&
      Object.keys(value).length <= MAX_ITEMS &&
      Object.entries(value).every(
        ([id, item]) => /^[A-Za-z0-9_.:-]{1,100}$/.test(id) && isBox(item),
      ),
    // Per question, the highest box; with the same box, the one that is due sooner.
    merge: (stored, incoming) => {
      const merged = {
        ...(stored as Record<string, { box: number; due: number }>),
      };
      for (const [id, item] of Object.entries(incoming as typeof merged)) {
        const old = merged[id];
        if (
          !old ||
          item.box > old.box ||
          (item.box === old.box && item.due < old.due)
        ) {
          merged[id] = { box: item.box, due: item.due };
        }
      }
      return merged;
    },
  },
];

const familyOf = (key: string) =>
  FAMILIES.find((family) => family.key.test(key));

const utf8Length = (text: string) => new TextEncoder().encode(text).length;

// Returns the validated progress or the reason it is not valid. It accepts no fields
// the server does not understand: a page bug shows up instead of being lost.
export function parseProgress(input: unknown): Progress | string {
  if (!isRecord(input)) return "El cuerpo debe ser un objeto JSON.";
  const unknown = Object.keys(input).find(
    (key) => !["done", "exercises", "kv"].includes(key),
  );
  if (unknown) return `Campo desconocido: ${unknown.slice(0, 40)}.`;
  const progress: Progress = { done: [], exercises: {}, kv: {} };

  if (input.done !== undefined) {
    const { done } = input;
    if (!Array.isArray(done) || done.length > MAX_DONE)
      return "done debe ser una lista corta.";
    if (!done.every((id) => typeof id === "string" && LESSON.test(id))) {
      return "done lleva un id de lección inválido.";
    }
    progress.done = [...new Set(done as string[])];
  }

  if (input.exercises !== undefined) {
    const { exercises } = input;
    if (!isRecord(exercises) || Object.keys(exercises).length > MAX_EXERCISES) {
      return "exercises debe ser un objeto corto.";
    }
    for (const [id, item] of Object.entries(exercises)) {
      if (!EXERCISE.test(id) || !isRecord(item))
        return "exercises lleva un ejercicio inválido.";
      const { code, hints, checks, passed, at } = item;
      const codeOk =
        code === undefined ||
        code === null ||
        (typeof code === "string" && utf8Length(code) <= MAX_CODE_BYTES);
      if (
        !codeOk ||
        !isInt(hints) ||
        !isInt(checks) ||
        typeof passed !== "boolean" ||
        !isInt(at)
      ) {
        return `El ejercicio ${id} tiene campos inválidos.`;
      }
      progress.exercises[id] = { code, hints, checks, passed, at };
    }
  }

  if (input.kv !== undefined) {
    const { kv } = input;
    if (!isRecord(kv) || Object.keys(kv).length > MAX_KV_KEYS)
      return "kv debe ser un objeto.";
    for (const [key, value] of Object.entries(kv)) {
      const family = familyOf(key);
      if (
        !family?.valid(value) ||
        utf8Length(JSON.stringify(value)) > MAX_KV_BYTES
      ) {
        return `kv lleva una clave o un valor inválido: ${key.slice(0, 60)}.`;
      }
      progress.kv[key] = value;
    }
  }
  return progress;
}

// The stored progress and the version it was read with, or null if the user does not
// exist. The four SELECTs run in one batch: they see the same state.
async function readState(
  db: D1Database,
  userId: string,
): Promise<{ progress: Progress; version: number } | null> {
  const [done, exercises, kv, user] = await db.batch<Record<string, unknown>>([
    db
      .prepare(
        "SELECT lesson FROM lesson_done WHERE user_id = ?1 ORDER BY lesson",
      )
      .bind(userId),
    db
      .prepare(
        "SELECT exercise, code, hints, checks, passed, updated_at FROM exercise_state WHERE user_id = ?1",
      )
      .bind(userId),
    db.prepare("SELECT key, value FROM kv WHERE user_id = ?1").bind(userId),
    db
      .prepare("SELECT progress_version AS version FROM users WHERE id = ?1")
      .bind(userId),
  ]);
  if (user.results.length === 0) return null;
  const progress: Progress = { done: [], exercises: {}, kv: {} };
  for (const row of done.results) progress.done.push(row.lesson as string);
  for (const row of exercises.results) {
    progress.exercises[row.exercise as string] = {
      ...(row.code === null ? {} : { code: row.code as string }),
      hints: row.hints as number,
      checks: row.checks as number,
      passed: row.passed === 1,
      at: row.updated_at as number,
    };
  }
  for (const row of kv.results)
    progress.kv[row.key as string] = JSON.parse(row.value as string);
  return { progress, version: user.results[0].version as number };
}

export async function readProgress(
  db: D1Database,
  userId: string,
): Promise<Progress | null> {
  return (await readState(db, userId))?.progress ?? null;
}

function mergeExercise(
  stored: ExerciseState | undefined,
  incoming: ExerciseState,
): ExerciseState {
  // The server records `passed`; the page's value is ignored.
  if (!stored) return { ...incoming, passed: false };
  const newer = incoming.at > stored.at;
  // Without code (`undefined` or null) the page did not send it: it does not erase the stored one.
  const code =
    newer && typeof incoming.code === "string" ? incoming.code : stored.code;
  return {
    ...(code === undefined || code === null ? {} : { code }),
    hints: Math.max(stored.hints, incoming.hints),
    checks: Math.max(stored.checks, incoming.checks),
    passed: stored.passed,
    at: Math.max(stored.at, incoming.at),
  };
}

export class TooMuch extends Error {}
// The user was deleted (DELETE /api/me or the purge) while the request ran.
export class Gone extends Error {}
// Other writes of the same user won every time.
export class Contended extends Error {}

const MAX_TRIES = 10;

// Merges `incoming` with the stored state and returns the resulting state. It reads,
// computes and writes in a batch whose statements act only if `progress_version` is
// still the one read; the last one raises it. D1 runs the batch without interleaving
// other writes, so if another request of the same user wrote in between, the last
// statement changes no row and the state is read again. No write overwrites another.
export async function mergeProgress(
  db: D1Database,
  userId: string,
  incoming: Progress,
  now: number,
): Promise<Progress> {
  for (let attempt = 0; attempt < MAX_TRIES; attempt++) {
    // oxlint-disable-next-line eslint/no-await-in-loop -- Each attempt rereads the state the previous one left.
    const state = await readState(db, userId);
    if (!state) throw new Gone();
    const { merged, statements } = plan(db, userId, state, incoming, now);
    if (statements.length === 0) return merged;
    statements.push(
      db
        .prepare(
          "UPDATE users SET progress_version = progress_version + 1 WHERE id = ?1 AND progress_version = ?2",
        )
        .bind(userId, state.version),
    );
    // oxlint-disable-next-line eslint/no-await-in-loop -- The next attempt depends on this result.
    const results = await db.batch(statements);
    if (results[results.length - 1].meta.changes === 1) return merged;
  }
  throw new Contended();
}

function plan(
  db: D1Database,
  userId: string,
  { progress: stored, version }: { progress: Progress; version: number },
  incoming: Progress,
  now: number,
): { merged: Progress; statements: D1PreparedStatement[] } {
  const merged: Progress = {
    done: [...stored.done],
    exercises: { ...stored.exercises },
    kv: { ...stored.kv },
  };

  const newDone = incoming.done.filter(
    (lesson) => !stored.done.includes(lesson),
  );
  merged.done = [...merged.done, ...newDone].toSorted();

  const exerciseRows: unknown[] = [];
  for (const [id, item] of Object.entries(incoming.exercises)) {
    const next = mergeExercise(stored.exercises[id], item);
    if (JSON.stringify(next) === JSON.stringify(stored.exercises[id])) continue;
    merged.exercises[id] = next;
    exerciseRows.push({
      exercise: id,
      code: next.code ?? null,
      hints: next.hints,
      checks: next.checks,
      at: next.at,
    });
  }

  const kvRows: unknown[] = [];
  for (const [key, value] of Object.entries(incoming.kv)) {
    const old = stored.kv[key];
    const next = old === undefined ? value : familyOf(key)!.merge(old, value);
    if (JSON.stringify(next) === JSON.stringify(old)) continue;
    merged.kv[key] = next;
    kvRows.push({ key, value: JSON.stringify(next) });
  }

  if (
    merged.done.length > MAX_DONE ||
    Object.keys(merged.exercises).length > MAX_EXERCISES ||
    Object.keys(merged.kv).length > MAX_KV_KEYS
  ) {
    throw new TooMuch();
  }

  // One statement per table: json_each spreads the array into rows. The WHERE
  // is the version guard (?4 in all of them).
  const current = "(SELECT progress_version FROM users WHERE id = ?1) = ?4";
  const statements: D1PreparedStatement[] = [];
  const seconds = unixSeconds(now);
  if (newDone.length) {
    statements.push(
      db
        .prepare(
          `INSERT INTO lesson_done (user_id, lesson, done_at)
           SELECT ?1, value, ?3 FROM json_each(?2) WHERE ${current}
           ON CONFLICT DO NOTHING`,
        )
        .bind(userId, JSON.stringify(newDone), seconds, version),
    );
  }
  if (exerciseRows.length) {
    statements.push(
      db
        .prepare(
          `INSERT INTO exercise_state (user_id, exercise, code, hints, checks, updated_at)
           SELECT ?1, value ->> '$.exercise', value ->> '$.code', value ->> '$.hints',
                  value ->> '$.checks', value ->> '$.at'
           FROM json_each(?2) WHERE ${current}
           ON CONFLICT (user_id, exercise) DO UPDATE SET
             code = excluded.code, hints = excluded.hints, checks = excluded.checks,
             updated_at = excluded.updated_at`,
        )
        .bind(userId, JSON.stringify(exerciseRows), seconds, version),
    );
  }
  if (kvRows.length) {
    statements.push(
      db
        .prepare(
          `INSERT INTO kv (user_id, key, value, updated_at)
           SELECT ?1, value ->> '$.key', value ->> '$.value', ?3 FROM json_each(?2) WHERE ${current}
           ON CONFLICT (user_id, key) DO UPDATE SET
             value = excluded.value, updated_at = excluded.updated_at`,
        )
        .bind(userId, JSON.stringify(kvRows), seconds, version),
    );
  }
  return { merged, statements };
}
