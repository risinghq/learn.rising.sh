"""Shows where learners get stuck, from the accounts' D1 database.

    uv run python tools/dashboard.py --database-id <uuid> [--since YYYY-MM-DD] [--until YYYY-MM-DD]
    uv run python tools/dashboard.py --local [--persist-to DIR]
    uv run python tools/dashboard.py --json ...

It reads with `wrangler d1 execute` (the one runner/worker installs) and writes nothing. By default
it reads the remote database, which needs a Cloudflare session and the database uuid
(`--database-id` or the QG_D1_ID variable). With `--local` it reads the local copy of
`wrangler dev`, or the one in `--persist-to`.

The period runs from `--since` to `--until`, both UTC days included. By default, the last 30 days.
It counts, in that period:
  - the new users, the users with any attempt and the attempts (with and without an account);
  - the lessons finished, per lesson: accounts only;
  - the exercises with the most failed checks and the cases that fail most. A failed check is a
    `check` attempt that did not end in `pass`; it counts without an account too;
  - the passed exercises with the most hints opened: accounts only, once per learner.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
WORKER = ROOT / "runner" / "worker"
DAY = 86400
DEFAULT_DAYS = 30

# {S} and {E} are Unix seconds. {E} is excluded. {SD} and {ED} are days since
# the epoch. {ED} is excluded. {N} is the row cap.
QUERIES = {
    "summary": """
        SELECT
          (SELECT COUNT(*) FROM users WHERE created_day >= {SD} AND created_day < {ED}) AS new_users,
          (SELECT COUNT(DISTINCT user_id) FROM attempts WHERE at >= {S} AND at < {E}) AS active_users,
          (SELECT COUNT(*) FROM attempts WHERE at >= {S} AND at < {E}) AS attempts,
          (SELECT COUNT(*) FROM attempts WHERE at >= {S} AND at < {E} AND user_id IS NULL)
            AS anonymous_attempts""",
    "completions": """
        SELECT lesson, COUNT(*) AS completions
        FROM lesson_done WHERE done_at >= {S} AND done_at < {E}
        GROUP BY lesson ORDER BY completions DESC, lesson""",
    "failed_checks": """
        SELECT exercise, COUNT(*) AS failed_checks, COUNT(DISTINCT user_id) AS users,
               SUM(user_id IS NULL) AS anonymous
        FROM attempts
        WHERE mode = 'check' AND outcome <> 'pass' AND at >= {S} AND at < {E}
        GROUP BY exercise ORDER BY failed_checks DESC, exercise LIMIT {N}""",
    "failed_cases": """
        SELECT a.exercise, j.value AS "case", COUNT(*) AS failures
        FROM attempts a, json_each(a.failed) j
        WHERE a.mode = 'check' AND a.at >= {S} AND a.at < {E}
        GROUP BY a.exercise, j.value ORDER BY failures DESC, a.exercise, j.value LIMIT {N}""",
    "hints_before_pass": """
        SELECT exercise, COUNT(*) AS passed_by, SUM(hints) AS hints,
               ROUND(AVG(hints), 2) AS hints_per_learner
        FROM exercise_state
        WHERE passed = 1 AND updated_at >= {S} * 1000 AND updated_at < {E} * 1000
        GROUP BY exercise HAVING SUM(hints) > 0
        ORDER BY hints DESC, exercise LIMIT {N}""",
}

# Title and columns of each section in the text.
SECTIONS = {
    "completions": ("Lessons finished", [("lesson", "lesson"), ("completions", "finished")]),
    "failed_checks": (
        "Exercises with the most failed checks",
        [
            ("exercise", "exercise"),
            ("failed_checks", "failed"),
            ("users", "with account"),
            ("anonymous", "anonymous"),
        ],
    ),
    "failed_cases": (
        "Cases that fail most",
        [("exercise", "exercise"), ("case", "case"), ("failures", "failures")],
    ),
    "hints_before_pass": (
        "Passed exercises with the most hints opened",
        [
            ("exercise", "exercise"),
            ("passed_by", "passed"),
            ("hints", "hints"),
            ("hints_per_learner", "per learner"),
        ],
    ),
}


def day_start(text: str) -> int:
    """Return the UTC start of a day written as YYYY-MM-DD."""
    try:
        day = datetime.datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        raise SystemExit(f"error: «{text}» is not a YYYY-MM-DD date") from None
    return int(day.replace(tzinfo=datetime.UTC).timestamp())


def period(since: str | None, until: str | None, today: str) -> tuple[int, int]:
    """Return the Unix interval that includes all of `until`."""
    end = (day_start(until) if until else day_start(today)) + DAY
    start = day_start(since) if since else end - DEFAULT_DAYS * DAY
    if start >= end:
        raise SystemExit("error: --since must be on or before --until")
    return start, end


def wrangler_json(args: argparse.Namespace) -> list[dict[str, Any]]:
    """Run Wrangler with a temporary configuration and return its JSON."""
    # Wrangler does not read cloudflare.config.ts. The temporary configuration declares the database.
    # The id only matters remotely.
    config = {
        "name": "qg-dashboard",
        "compatibility_date": "2026-10-01",
        "d1_databases": [
            {
                "binding": "DB",
                "database_name": args.database,
                "database_id": args.database_id or "00000000-0000-0000-0000-000000000000",
            }
        ],
    }
    sql = ";\n".join(" ".join(q.format(**args.bounds).split()) for q in QUERIES.values())
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "wrangler.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        cmd = ["bunx", "wrangler", "d1", "execute", args.database, "--config", str(path), "--json"]
        if args.local:
            persist = Path(args.persist_to or WORKER / ".wrangler" / "state").resolve()
            cmd += ["--local", "--persist-to", str(persist)]
        else:
            cmd += ["--remote"]
        cmd += ["--command", sql]
        run = subprocess.run(cmd, cwd=WORKER, capture_output=True, text=True)
    if run.returncode != 0:
        sys.stderr.write(run.stdout + run.stderr)
        raise SystemExit(f"error: wrangler exited with code {run.returncode}")
    answers: list[dict[str, Any]] = json.loads(run.stdout)
    return answers


def collect(args: argparse.Namespace) -> dict[str, Any]:
    """Turn Wrangler's answers into the report."""
    answers = wrangler_json(args)
    if len(answers) != len(QUERIES):
        raise SystemExit(f"error: wrangler returned {len(answers)} answers out of {len(QUERIES)}")
    rows: dict[str, Any] = {}
    for name, answer in zip(QUERIES, answers, strict=True):
        if not answer.get("success", False):
            raise SystemExit(f"error: query {name} failed: {answer}")
        rows[name] = answer["results"]

    def day(seconds: int) -> datetime.date:
        return datetime.datetime.fromtimestamp(seconds, datetime.UTC).date()

    start, end = args.bounds["S"], args.bounds["E"]
    return {
        "period": {"since": day(start).isoformat(), "until": day(end - DAY).isoformat()},
        "summary": rows.pop("summary")[0],
        **rows,
    }


def table(rows: Sequence[dict[str, Any]], columns: Sequence[tuple[str, str]]) -> list[str]:
    """Return aligned lines with text on the left and numbers on the right."""
    cells = [[str(row[key]) for key, _ in columns] for row in rows]
    heads = [head for _, head in columns]
    widths = [max(len(c[i]) for c in [heads, *cells]) for i in range(len(columns))]
    numeric = [all(isinstance(row[key], (int, float)) for row in rows) for key, _ in columns]

    def line(values: Sequence[str]) -> str:
        parts = [
            v.rjust(w) if n else v.ljust(w) for v, w, n in zip(values, widths, numeric, strict=True)
        ]
        return ("  ".join(parts)).rstrip()

    return [line(heads), *map(line, cells)]


def render(report: dict[str, Any]) -> str:
    """Render the report as aligned text."""
    period, summary = report["period"], report["summary"]
    out = [f"Period: {period['since']} to {period['until']} (UTC)", ""]
    labels = [
        ("new_users", "New users"),
        ("active_users", "Users with attempts"),
        ("attempts", "Attempts"),
        ("anonymous_attempts", "Attempts without account"),
    ]
    width = max(len(label) for _, label in labels)
    out += [f"{label.ljust(width)}  {summary[key]}" for key, label in labels]
    for key, (title, columns) in SECTIONS.items():
        out += ["", title]
        rows = report[key]
        out += table(rows, columns) if rows else ["(none)"]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--since", help="first day, YYYY-MM-DD (default: 30 days up to --until)")
    ap.add_argument("--until", help="last day included, YYYY-MM-DD (default: today)")
    ap.add_argument("--limit", type=int, default=10, help="rows per section (default: 10)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    ap.add_argument("--local", action="store_true", help="read the local database, not the remote")
    ap.add_argument("--persist-to", help="with --local, the directory of wrangler's local state")
    ap.add_argument("--database", default="qiskit-guides", help="the name of the D1 database")
    ap.add_argument("--database-id", default=os.environ.get("QG_D1_ID"), help="the uuid (remote)")
    args = ap.parse_args()
    if not args.local and not args.database_id:
        ap.error("the remote database needs --database-id or QG_D1_ID")
    if args.limit < 1:
        ap.error("--limit must be positive")

    today = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    start, end = period(args.since, args.until, today)
    args.bounds = {"S": start, "E": end, "SD": start // DAY, "ED": end // DAY, "N": args.limit}
    report = collect(args)
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render(report))


if __name__ == "__main__":
    main()
