// Shows where learners get stuck, from the accounts' D1 database.
//     bun tools/dashboard.ts --database-id <uuid> [--since YYYY-MM-DD] [--until YYYY-MM-DD]
//     bun tools/dashboard.ts --local [--persist-to DIR] [--json]
// Read-only, through `wrangler d1 execute`. Remote by default (needs a Cloudflare
// session and `--database-id` or QG_D1_ID); `--local` reads `wrangler dev`'s copy
// or `--persist-to`. The period, UTC days included, is 30 days by default.
import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { parseArgs } from "node:util";

const ROOT = resolve(import.meta.dirname, "..");
const WORKER = join(ROOT, "runner", "worker");
const DAY = 86400;
const DEFAULT_DAYS = 30;

interface Bounds {
  S: number;
  E: number;
  SD: number;
  ED: number;
  N: number;
}
type Row = Record<string, string | number | null>;
interface Report {
  period: { since: string; until: string };
  summary: Row;
  completions: Row[];
  failed_checks: Row[];
  failed_cases: Row[];
  hints_before_pass: Row[];
}
type Section = Exclude<keyof Report, "period" | "summary">;
interface Options {
  since?: string;
  until?: string;
  limit: number;
  json: boolean;
  local: boolean;
  persistTo?: string;
  database: string;
  databaseId?: string;
}
interface Answer {
  success?: boolean;
  results: Row[];
}

// {S} and {E} are Unix seconds. {E} is excluded. {SD} and {ED} are days since
// the epoch. {ED} is excluded. {N} is the row cap.
const QUERIES: Record<"summary" | Section, string> = {
  summary: `
        SELECT
          (SELECT COUNT(*) FROM users WHERE created_day >= {SD} AND created_day < {ED}) AS new_users,
          (SELECT COUNT(DISTINCT user_id) FROM attempts WHERE at >= {S} AND at < {E}) AS active_users,
          (SELECT COUNT(*) FROM attempts WHERE at >= {S} AND at < {E}) AS attempts,
          (SELECT COUNT(*) FROM attempts WHERE at >= {S} AND at < {E} AND user_id IS NULL)
            AS anonymous_attempts`,
  completions: `
        SELECT lesson, COUNT(*) AS completions
        FROM lesson_done WHERE done_at >= {S} AND done_at < {E}
        GROUP BY lesson ORDER BY completions DESC, lesson`,
  failed_checks: `
        SELECT exercise, COUNT(*) AS failed_checks, COUNT(DISTINCT user_id) AS users,
               SUM(user_id IS NULL) AS anonymous
        FROM attempts
        WHERE mode = 'check' AND outcome <> 'pass' AND at >= {S} AND at < {E}
        GROUP BY exercise ORDER BY failed_checks DESC, exercise LIMIT {N}`,
  failed_cases: `
        SELECT a.exercise, j.value AS "case", COUNT(*) AS failures
        FROM attempts a, json_each(a.failed) j
        WHERE a.mode = 'check' AND a.at >= {S} AND a.at < {E}
        GROUP BY a.exercise, j.value ORDER BY failures DESC, a.exercise, j.value LIMIT {N}`,
  hints_before_pass: `
        SELECT exercise, COUNT(*) AS passed_by, SUM(hints) AS hints,
               ROUND(AVG(hints), 2) AS hints_per_learner
        FROM exercise_state
        WHERE passed = 1 AND updated_at >= {S} * 1000 AND updated_at < {E} * 1000
        GROUP BY exercise HAVING SUM(hints) > 0
        ORDER BY hints DESC, exercise LIMIT {N}`,
};

const SECTIONS: Record<Section, [string, [key: string, head: string][]]> = {
  completions: [
    "Lessons finished",
    [
      ["lesson", "lesson"],
      ["completions", "finished"],
    ],
  ],
  failed_checks: [
    "Exercises with the most failed checks",
    [
      ["exercise", "exercise"],
      ["failed_checks", "failed"],
      ["users", "with account"],
      ["anonymous", "anonymous"],
    ],
  ],
  failed_cases: [
    "Cases that fail most",
    [
      ["exercise", "exercise"],
      ["case", "case"],
      ["failures", "failures"],
    ],
  ],
  hints_before_pass: [
    "Passed exercises with the most hints opened",
    [
      ["exercise", "exercise"],
      ["passed_by", "passed"],
      ["hints", "hints"],
      ["hints_per_learner", "per learner"],
    ],
  ],
};

function fail(message: string, code = 1): never {
  console.error(message);
  process.exit(code);
}

function dayStart(text: string): number {
  const match = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(text);
  if (match) {
    const [year, month, day] = match.slice(1).map(Number);
    const date = new Date(Date.UTC(year, month - 1, day));
    if (date.getUTCMonth() === month - 1 && date.getUTCDate() === day) {
      return date.getTime() / 1000;
    }
  }
  return fail(`error: «${text}» is not a YYYY-MM-DD date`);
}

function period(
  since: string | undefined,
  until: string | undefined,
  today: string,
): [number, number] {
  const end = dayStart(until ?? today) + DAY;
  const start = since ? dayStart(since) : end - DEFAULT_DAYS * DAY;
  if (start >= end) fail("error: --since must be on or before --until");
  return [start, end];
}

function wranglerJson(options: Options, bounds: Bounds): Answer[] {
  // Wrangler does not read cloudflare.config.ts. The temporary configuration declares the database.
  // The id only matters remotely.
  const config = {
    name: "qg-dashboard",
    compatibility_date: "2026-10-01",
    d1_databases: [
      {
        binding: "DB",
        database_name: options.database,
        database_id:
          options.databaseId ?? "00000000-0000-0000-0000-000000000000",
      },
    ],
  };
  const sql = Object.values(QUERIES)
    .map((query) =>
      query
        .replace(/\{(\w+)\}/g, (_, key: keyof Bounds) => String(bounds[key]))
        .trim()
        .replace(/\s+/g, " "),
    )
    .join(";\n");
  const scratch = mkdtempSync(join(tmpdir(), "qg-dashboard-"));
  try {
    const path = join(scratch, "wrangler.json");
    writeFileSync(path, JSON.stringify(config));
    const command = [
      "wrangler",
      "d1",
      "execute",
      options.database,
      "--config",
      path,
      "--json",
    ];
    if (options.local) {
      const persist = resolve(
        options.persistTo ?? join(WORKER, ".wrangler", "state"),
      );
      command.push("--local", "--persist-to", persist);
    } else {
      command.push("--remote");
    }
    command.push("--command", sql);
    const run = spawnSync("bunx", command, {
      cwd: WORKER,
      encoding: "utf8",
      maxBuffer: 64 * 1024 * 1024,
    });
    if (run.status !== 0) {
      process.stderr.write(run.stdout + run.stderr);
      fail(`error: wrangler exited with code ${run.status ?? run.signal}`);
    }
    return JSON.parse(run.stdout) as Answer[];
  } finally {
    rmSync(scratch, { recursive: true, force: true });
  }
}

const isoDay = (seconds: number): string =>
  new Date(seconds * 1000).toISOString().slice(0, 10);

function collect(options: Options, bounds: Bounds): Report {
  const answers = wranglerJson(options, bounds);
  const names = Object.keys(QUERIES) as (keyof typeof QUERIES)[];
  if (answers.length !== names.length) {
    fail(
      `error: wrangler returned ${answers.length} answers out of ${names.length}`,
    );
  }
  const rows = {} as Record<keyof typeof QUERIES, Row[]>;
  names.forEach((name, i) => {
    if (!(answers[i].success ?? false)) {
      fail(`error: query ${name} failed: ${JSON.stringify(answers[i])}`);
    }
    rows[name] = answers[i].results;
  });
  const { summary, ...sections } = rows;
  return {
    period: { since: isoDay(bounds.S), until: isoDay(bounds.E - DAY) },
    summary: summary[0],
    ...sections,
  };
}

function table(rows: Row[], columns: [key: string, head: string][]): string[] {
  const cells = rows.map((row) => columns.map(([key]) => String(row[key])));
  const heads = columns.map(([, head]) => head);
  const widths = columns.map((_, i) =>
    Math.max(...[heads, ...cells].map((line) => line[i].length)),
  );
  const numeric = columns.map(([key]) =>
    rows.every((row) => typeof row[key] === "number"),
  );
  const line = (values: string[]): string =>
    values
      .map((v, i) => (numeric[i] ? v.padStart(widths[i]) : v.padEnd(widths[i])))
      .join("  ")
      .trimEnd();
  return [line(heads), ...cells.map(line)];
}

function render(report: Report): string {
  const { period: days, summary } = report;
  const out = [`Period: ${days.since} to ${days.until} (UTC)`, ""];
  const labels = [
    ["new_users", "New users"],
    ["active_users", "Users with attempts"],
    ["attempts", "Attempts"],
    ["anonymous_attempts", "Attempts without account"],
  ];
  const width = Math.max(...labels.map(([, label]) => label.length));
  out.push(
    ...labels.map(([key, label]) => `${label.padEnd(width)}  ${summary[key]}`),
  );
  for (const [key, [title, columns]] of Object.entries(SECTIONS) as [
    Section,
    (typeof SECTIONS)[Section],
  ][]) {
    out.push("", title);
    const rows = report[key];
    out.push(...(rows.length ? table(rows, columns) : ["(none)"]));
  }
  return out.join("\n");
}

const usage = (message: string): never =>
  fail(`dashboard.ts: error: ${message}`, 2);

function parseValues() {
  try {
    return parseArgs({
      options: {
        since: { type: "string" },
        until: { type: "string" },
        limit: { type: "string", default: "10" },
        json: { type: "boolean" },
        local: { type: "boolean" },
        "persist-to": { type: "string" },
        database: { type: "string", default: "qiskit-guides" },
        "database-id": { type: "string", default: process.env.QG_D1_ID },
      },
    }).values;
  } catch (error) {
    return usage(error instanceof Error ? error.message : String(error));
  }
}

function parse(): Options {
  const values = parseValues();
  const limit = Number(values.limit);
  if (!Number.isInteger(limit)) {
    usage(`argument --limit: invalid int value: '${values.limit}'`);
  }
  const options: Options = {
    since: values.since,
    until: values.until,
    limit,
    json: values.json ?? false,
    local: values.local ?? false,
    persistTo: values["persist-to"],
    database: values.database,
    databaseId: values["database-id"] || undefined,
  };
  if (!options.local && !options.databaseId) {
    usage("the remote database needs --database-id or QG_D1_ID");
  }
  if (options.limit < 1) usage("--limit must be positive");
  return options;
}

function main(): void {
  const options = parse();
  const today = new Date().toISOString().slice(0, 10);
  const [start, end] = period(options.since, options.until, today);
  const bounds: Bounds = {
    S: start,
    E: end,
    SD: Math.floor(start / DAY),
    ED: Math.floor(end / DAY),
    N: options.limit,
  };
  const report = collect(options, bounds);
  console.log(options.json ? JSON.stringify(report, null, 2) : render(report));
}

main();
