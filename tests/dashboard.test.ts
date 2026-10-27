// Tests tools/dashboard.ts against a local D1 database with the Worker's schema
// and known rows: bunx vitest run tests/dashboard.test.ts
// It needs the wrangler that `mise run install` puts in runner/worker, and is
// skipped without it.
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

import { afterAll, beforeAll, describe, expect, test } from "vitest";

const ROOT = resolve(import.meta.dirname, "..");
const WORKER = join(ROOT, "runner", "worker");
const TOOL = join(ROOT, "tools", "dashboard.ts");

const hasBun = spawnSync("bun", ["--version"]).error === undefined;
const hasWrangler = existsSync(
  join(WORKER, "node_modules", ".bin", "wrangler"),
);

const at = (day: number, hour = 12): number =>
  Date.UTC(2026, 9, day, hour) / 1000;

const epochDay = (day: number): number => Math.floor(at(day, 0) / 86400);

function attempt(
  day: number,
  user: string | null,
  exercise: string,
  mode: string,
  outcome: string,
  failed: string[] = [],
  hints = 0,
): string {
  const cases = JSON.stringify(failed).replaceAll("'", "''");
  const who = user ? `'${user}'` : "NULL";
  return (
    "INSERT INTO attempts (at, user_id, exercise, mode, outcome, failed, hints, ms, code_bytes) " +
    `VALUES (${at(day)}, ${who}, '${exercise}', '${mode}', '${outcome}', '${cases}', ${hints}, 10, 100)`
  );
}

function state(
  user: string,
  exercise: string,
  hints: number,
  passed: number,
  day: number,
): string {
  return (
    "INSERT INTO exercise_state (user_id, exercise, hints, checks, passed, updated_at) " +
    `VALUES ('${user}', '${exercise}', ${hints}, 1, ${passed}, ${at(day) * 1000})`
  );
}

const SEED = [
  "INSERT INTO users (id, created_day, seen_day) VALUES " +
    `('u1', ${epochDay(5)}, ${epochDay(9)}), ('u2', ${epochDay(11)}, ${epochDay(11)}), ` +
    `('u3', ${epochDay(4)}, ${epochDay(9)}), ('u4', ${epochDay(12)}, ${epochDay(12)})`,
  // These rows distinguish account failures, anonymous failures, failed cases, errors, and timeouts.
  attempt(6, "u1", "p1/ghz", "check", "fail", ["chain", "measure"]),
  attempt(7, "u1", "p1/ghz", "check", "fail", ["chain"]),
  attempt(8, "u2", "p1/ghz", "check", "fail", ["size", "measure"]),
  attempt(9, null, "p1/ghz", "check", "fail", ["chain"]),
  attempt(9, "u1", "p1/ghz", "check", "pass"),
  attempt(10, null, "p1/bell", "check", "error"),
  attempt(10, "u2", "p1/bell", "check", "timeout"),
  attempt(10, "u1", "p1/ghz", "run", "fail", ["chain"]),
  attempt(10, null, "p1/bell", "check", "pass"),
  attempt(4, "u3", "p1/ghz", "check", "fail", ["chain"]),
  attempt(12, "u4", "p1/ghz", "check", "fail", ["chain"]),
  "INSERT INTO lesson_done (user_id, lesson, done_at) VALUES " +
    `('u1', 'p1', ${at(7)}), ('u2', 'p1', ${at(9)}), ('u1', 'p2', ${at(8)}), ` +
    `('u3', 'p1', ${at(4)}), ('u4', 'p3', ${at(12)})`,
  state("u1", "p1/ghz", 3, 1, 9),
  state("u2", "p1/ghz", 2, 1, 10),
  state("u1", "p1/bell", 0, 1, 9),
  state("u2", "p1/bell", 5, 0, 10),
  state("u3", "p1/ghz", 4, 1, 4),
];

const PERIOD = ["--since", "2026-10-05", "--until", "2026-10-11"];

const EXPECTED = {
  period: { since: "2026-10-05", until: "2026-10-11" },
  summary: {
    new_users: 2,
    active_users: 2,
    attempts: 9,
    anonymous_attempts: 3,
  },
  completions: [
    { lesson: "p1", completions: 2 },
    { lesson: "p2", completions: 1 },
  ],
  failed_checks: [
    { exercise: "p1/ghz", failed_checks: 4, users: 2, anonymous: 1 },
    { exercise: "p1/bell", failed_checks: 2, users: 1, anonymous: 1 },
  ],
  failed_cases: [
    { exercise: "p1/ghz", case: "chain", failures: 3 },
    { exercise: "p1/ghz", case: "measure", failures: 2 },
    { exercise: "p1/ghz", case: "size", failures: 1 },
  ],
  hints_before_pass: [
    { exercise: "p1/ghz", passed_by: 2, hints: 5, hints_per_learner: 2.5 },
  ],
};

const TEXT = `\
Period: 2026-10-05 to 2026-10-11 (UTC)

New users                 2
Users with attempts       2
Attempts                  9
Attempts without account  3

Lessons finished
lesson  finished
p1             2
p2             1

Exercises with the most failed checks
exercise  failed  with account  anonymous
p1/ghz         4             2          1
p1/bell        2             1          1

Cases that fail most
exercise  case     failures
p1/ghz    chain           3
p1/ghz    measure         2
p1/ghz    size            1

Passed exercises with the most hints opened
exercise  passed  hints  per learner
p1/ghz         2      5          2.5`;

function wrangler(scratch: string, ...args: string[]): void {
  const config = join(scratch, "wrangler.json");
  writeFileSync(
    config,
    JSON.stringify({
      name: "qg-dashboard-test",
      compatibility_date: "2026-10-01",
      d1_databases: [
        {
          binding: "DB",
          database_name: "test",
          database_id: "00000000-0000-0000-0000-000000000000",
        },
      ],
    }),
  );
  const done = spawnSync(
    "bunx",
    [
      "wrangler",
      "d1",
      "execute",
      "test",
      "--config",
      config,
      "--local",
      "--persist-to",
      join(scratch, "state"),
      ...args,
    ],
    { cwd: WORKER, encoding: "utf8" },
  );
  expect(done.status, done.stdout + done.stderr).toBe(0);
}

function run(args: string[], env: Record<string, string> = {}) {
  return spawnSync("bun", [TOOL, ...args], {
    encoding: "utf8",
    env: { ...process.env, ...env },
  });
}

describe.skipIf(!hasBun || !hasWrangler)("dashboard", () => {
  let scratch = "";

  beforeAll(() => {
    scratch = mkdtempSync(join(tmpdir(), "qg-d1-"));
    wrangler(scratch, "--file", join(WORKER, "src", "schema.sql"));
    const seed = join(scratch, "seed.sql");
    writeFileSync(seed, `${SEED.join(";\n")};\n`);
    wrangler(scratch, "--file", seed);
  }, 180_000);

  afterAll(() => rmSync(scratch, { recursive: true, force: true }));

  function dashboard(...args: string[]): string {
    const done = run([
      "--local",
      "--persist-to",
      join(scratch, "state"),
      "--database",
      "test",
      ...args,
    ]);
    expect(done.status, done.stdout + done.stderr).toBe(0);
    return done.stdout;
  }

  test("json rows", () => {
    const out: unknown = JSON.parse(dashboard("--json", ...PERIOD));
    expect(out).toEqual(EXPECTED);
  });

  test("text report", () => {
    expect(dashboard(...PERIOD).replace(/\n+$/, "")).toBe(TEXT);
  });

  test("limit cuts every ranking", () => {
    const out: typeof EXPECTED = JSON.parse(
      dashboard("--json", "--limit", "1", ...PERIOD),
    );
    expect(out.failed_checks).toEqual(EXPECTED.failed_checks.slice(0, 1));
    expect(out.failed_cases).toEqual(EXPECTED.failed_cases.slice(0, 1));
    expect(out.completions).toEqual(EXPECTED.completions);
  });

  test("an empty period prints zeros", () => {
    const out: typeof EXPECTED = JSON.parse(
      dashboard("--json", "--since", "2026-09-01", "--until", "2026-09-02"),
    );
    expect(out.summary).toEqual({
      new_users: 0,
      active_users: 0,
      attempts: 0,
      anonymous_attempts: 0,
    });
    expect(out.completions).toEqual([]);
    expect(out.failed_checks).toEqual([]);
    expect(out.failed_cases).toEqual([]);
    expect(out.hints_before_pass).toEqual([]);
  });
});

describe.skipIf(!hasBun)("dashboard arguments", () => {
  test("the remote database needs a database id", () => {
    const done = run([], { QG_D1_ID: "" });
    expect(done.status).toBe(2);
    expect(done.stderr).toContain("--database-id");
  });
});
