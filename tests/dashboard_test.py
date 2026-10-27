"""Tests tools/dashboard.py against a local D1 database with the Worker's schema and known rows.

    uv run pytest tests/dashboard_test.py

It needs `mise run install`, which brings wrangler to runner/worker; without it, it is skipped.
"""

import datetime
import json
import shutil
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
WORKER = ROOT / "runner" / "worker"
TOOL = ROOT / "tools" / "dashboard.py"

pytestmark = pytest.mark.skipif(
    not shutil.which("bunx") or not (WORKER / "node_modules" / ".bin" / "wrangler").exists(),
    reason="bun or wrangler is missing: run `mise run install`",
)


def at(day: int, hour: int = 12) -> int:
    """Unix seconds of a day in October 2026 at a UTC hour."""
    moment = datetime.datetime(2026, 10, day, hour, tzinfo=datetime.UTC)
    return int(moment.timestamp())


def epoch_day(day: int) -> int:
    return at(day, 0) // 86400


def attempt(
    day: int,
    user: str | None,
    exercise: str,
    mode: str,
    outcome: str,
    failed: Iterable[str] = (),
    hints: int = 0,
) -> str:
    cases = json.dumps(list(failed)).replace("'", "''")
    who = f"'{user}'" if user else "NULL"
    return (
        "INSERT INTO attempts (at, user_id, exercise, mode, outcome, failed, hints, ms, code_bytes) "
        f"VALUES ({at(day)}, {who}, '{exercise}', '{mode}', '{outcome}', '{cases}', {hints}, 10, 100)"
    )


def state(user: str, exercise: str, hints: int, passed: int, day: int) -> str:
    return (
        "INSERT INTO exercise_state (user_id, exercise, hints, checks, passed, updated_at) "
        f"VALUES ('{user}', '{exercise}', {hints}, 1, {passed}, {at(day) * 1000})"
    )


# Test period: 5 to 11 October, both included.
SEED = [
    "INSERT INTO users (id, created_day, seen_day) VALUES "
    f"('u1', {epoch_day(5)}, {epoch_day(9)}), ('u2', {epoch_day(11)}, {epoch_day(11)}), "
    f"('u3', {epoch_day(4)}, {epoch_day(9)}), ('u4', {epoch_day(12)}, {epoch_day(12)})",
    # Inside the period: p1/ghz fails 4 times (u1 twice, u2 once, one anonymous), with the cases
    # «chain» (3), «measure» (2) and «size» (1); p1/bell fails once by error and once by timeout.
    attempt(6, "u1", "p1/ghz", "check", "fail", ["chain", "measure"]),
    attempt(7, "u1", "p1/ghz", "check", "fail", ["chain"]),
    attempt(8, "u2", "p1/ghz", "check", "fail", ["size", "measure"]),
    attempt(9, None, "p1/ghz", "check", "fail", ["chain"]),
    attempt(9, "u1", "p1/ghz", "check", "pass"),
    attempt(10, None, "p1/bell", "check", "error"),
    attempt(10, "u2", "p1/bell", "check", "timeout"),
    # Not failed checks: a run that was not checked and one that passes.
    attempt(10, "u1", "p1/ghz", "run", "fail", ["chain"]),
    attempt(10, None, "p1/bell", "check", "pass"),
    # Outside the period.
    attempt(4, "u3", "p1/ghz", "check", "fail", ["chain"]),
    attempt(12, "u4", "p1/ghz", "check", "fail", ["chain"]),
    "INSERT INTO lesson_done (user_id, lesson, done_at) VALUES "
    f"('u1', 'p1', {at(7)}), ('u2', 'p1', {at(9)}), ('u1', 'p2', {at(8)}), "
    f"('u3', 'p1', {at(4)}), ('u4', 'p3', {at(12)})",
    # Learners who passed: u1 and u2 opened hints in p1/ghz, u1 none in p1/bell.
    state("u1", "p1/ghz", 3, 1, 9),
    state("u2", "p1/ghz", 2, 1, 10),
    state("u1", "p1/bell", 0, 1, 9),
    state("u2", "p1/bell", 5, 0, 10),
    state("u3", "p1/ghz", 4, 1, 4),
]

PERIOD = ["--since", "2026-10-05", "--until", "2026-10-11"]

EXPECTED: dict[str, Any] = {
    "period": {"since": "2026-10-05", "until": "2026-10-11"},
    "summary": {"new_users": 2, "active_users": 2, "attempts": 9, "anonymous_attempts": 3},
    "completions": [
        {"lesson": "p1", "completions": 2},
        {"lesson": "p2", "completions": 1},
    ],
    "failed_checks": [
        {"exercise": "p1/ghz", "failed_checks": 4, "users": 2, "anonymous": 1},
        {"exercise": "p1/bell", "failed_checks": 2, "users": 1, "anonymous": 1},
    ],
    "failed_cases": [
        {"exercise": "p1/ghz", "case": "chain", "failures": 3},
        {"exercise": "p1/ghz", "case": "measure", "failures": 2},
        {"exercise": "p1/ghz", "case": "size", "failures": 1},
    ],
    "hints_before_pass": [
        {"exercise": "p1/ghz", "passed_by": 2, "hints": 5, "hints_per_learner": 2.5},
    ],
}

TEXT = """\
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
p1/ghz         2      5          2.5"""


def wrangler(persist: Path, *args: str) -> None:
    config = persist / "wrangler.json"
    config.write_text(
        json.dumps(
            {
                "name": "qg-dashboard-test",
                "compatibility_date": "2026-10-01",
                "d1_databases": [
                    {
                        "binding": "DB",
                        "database_name": "test",
                        "database_id": "0" * 8 + "-0000-0000-0000-" + "0" * 12,
                    }
                ],
            }
        )
    )
    cmd = ["bunx", "wrangler", "d1", "execute", "test", "--config", str(config), "--local"]
    cmd += ["--persist-to", str(persist / "state"), *args]
    done = subprocess.run(cmd, cwd=WORKER, capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr


@pytest.fixture(scope="module")
def persist(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("d1")
    wrangler(path, "--file", str(WORKER / "src" / "schema.sql"))
    seed = path / "seed.sql"
    seed.write_text(";\n".join(SEED) + ";\n")
    wrangler(path, "--file", str(seed))
    return path / "state"


def dashboard(persist: Path, *args: str) -> str:
    cmd = [sys.executable, str(TOOL), "--local", "--persist-to", str(persist), "--database", "test"]
    done = subprocess.run([*cmd, *args], capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr
    return done.stdout


def test_json_rows(persist: Path) -> None:
    out = json.loads(dashboard(persist, "--json", *PERIOD))
    assert out == EXPECTED


def test_text_report(persist: Path) -> None:
    assert dashboard(persist, *PERIOD).rstrip("\n") == TEXT


def test_limit_cuts_every_ranking(persist: Path) -> None:
    out = json.loads(dashboard(persist, "--json", "--limit", "1", *PERIOD))
    assert out["failed_checks"] == EXPECTED["failed_checks"][:1]
    assert out["failed_cases"] == EXPECTED["failed_cases"][:1]
    assert out["completions"] == EXPECTED["completions"]


def test_empty_period_prints_zeros(persist: Path) -> None:
    out = json.loads(dashboard(persist, "--json", "--since", "2026-09-01", "--until", "2026-09-02"))
    assert out["summary"] == {
        "new_users": 0,
        "active_users": 0,
        "attempts": 0,
        "anonymous_attempts": 0,
    }
    assert out["completions"] == out["failed_checks"] == out["failed_cases"] == []
    assert out["hints_before_pass"] == []


def test_remote_needs_a_database_id() -> None:
    done = subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True)
    assert done.returncode == 2
    assert "--database-id" in done.stderr
