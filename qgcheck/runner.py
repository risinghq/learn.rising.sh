"""Run a learner's code against an exercise, in a separate process.

    from qgcheck import grade
    grade("p1-quickstart/ghz", code, mode="check")

The result:

    {"passed": bool, "stdout": str, "error": str | None, "ms": int, "killed": str | None,
     "tests": [{"name": str, "visible": bool, "passed": bool, "message": str | None,
                "hint": int | None}]}

`mode="run"` only runs the code and returns its output; `tests` stays empty.
`mode="check"` also runs the cases of check.py. With `block` the named modules cannot be
imported in the learner's process.

`grade` launches `python -m qgcheck.job`, the same job the runner (runner/server.py) launches with
uid, memory and network limits. `timeout` counts from the start of the process, libraries
included. Here the job runs as your user, without those limits: it keeps the learner's interpreter
apart from the caller's, and is not a security isolation. Whoever exposes this on a network must
use the runner, in a container with no network.
"""

import contextlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from qgcheck import spec
from qgcheck.source import stopped

MAX_CODE = 20_000
TIMEOUT = 10
OUT_BYTES = 64 * 1024
REPORT_CAP = 2**20
MESSAGE_CAP = 500
POLL = 0.02
ROOT = Path(__file__).resolve().parent.parent
NOT_FINISHED = "El código no terminó: se quedó sin memoria o el proceso se cerró."


def job_argv(mode: str, code_path: str, check_path: str | None = None) -> list[str]:
    return [
        sys.executable,
        "-u",
        "-P",
        "-m",
        "qgcheck.job",
        mode,
        code_path,
        *([check_path] if check_path else []),
    ]


def job_env(work: str, path: str) -> dict[str, str]:
    return {
        "PATH": path,
        "HOME": work,
        "TMPDIR": work,
        "MPLCONFIGDIR": work,
        "LANG": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONUNBUFFERED": "1",
        "PYTHONPATH": str(ROOT),
        "MPLBACKEND": "Agg",
        "OMP_NUM_THREADS": "2",
        "OPENBLAS_NUM_THREADS": "2",
        "RAYON_NUM_THREADS": "2",
    }


def font_cache() -> Path:
    """The directory where local jobs keep matplotlib's font list.

    A job's own directory is empty, so every job would scan the host's fonts again: 0.5 s of CPU
    with a few hundred system fonts, more than the rest of a plot. The runner's container has no
    system fonts, so there the scan is short and each job keeps its own directory.
    """
    cache = Path(tempfile.gettempdir()) / f"qgcheck-matplotlib-{os.getuid()}"
    cache.mkdir(mode=0o700, exist_ok=True)
    return cache


def drain(fd: int, cap: int, box: bytearray, over: threading.Event) -> None:
    while True:
        try:
            chunk = os.read(fd, 65536)
        except OSError:
            break
        if not chunk:
            break
        room = cap - len(box)
        box.extend(chunk[:room])
        if len(chunk) > room:
            over.set()


def parse_report(raw: bytes) -> tuple[str | None, list[dict[str, Any]]] | None:
    """Validate what the job wrote; in `run` the learner controls it.

    Return (error, cases), or None if there is no valid report.
    """
    try:
        report = json.loads(raw)
        error, items = report["error"], report["tests"]
    except ValueError, KeyError, TypeError:
        return None
    if not (error is None or isinstance(error, str)) or not isinstance(items, list):
        return None
    tests: list[dict[str, Any]] = []
    for t in items:
        if not isinstance(t, dict):
            continue
        name, message, hint = t.get("name"), t.get("message"), t.get("hint")
        tests.append(
            {
                "name": name[:MESSAGE_CAP] if isinstance(name, str) else None,
                "visible": t.get("visible") is True,
                "passed": t.get("passed") is True,
                "message": message[:MESSAGE_CAP] if isinstance(message, str) else None,
                "hint": hint if type(hint) is int and hint >= 1 else None,
            }
        )
    return error and error[:MESSAGE_CAP], tests


def result(
    mode: str, raw: bytes, output: str, killed: str | None, why: str | None, ms: int
) -> dict[str, Any]:
    report = parse_report(raw)
    error: str | None
    tests: list[dict[str, Any]]
    if killed:
        error, tests = why, []
    elif report is None:
        error, tests = NOT_FINISHED, []
    else:
        error, tests = report
    if mode == "run":
        tests = []
    return {
        "passed": error is None
        and (mode == "run" or (bool(tests) and all(t["passed"] for t in tests))),
        "stdout": output,
        "error": error,
        "tests": tests,
        "ms": ms,
        "killed": killed,
    }


def grade(
    exercise_id: str,
    code: str,
    mode: str = "check",
    block: Iterable[str] = (),
    timeout: float = TIMEOUT,
) -> dict[str, Any]:
    start = time.monotonic()
    if mode not in ("run", "check"):
        raise ValueError(f"invalid mode: {mode!r}")
    d = spec.folder(exercise_id)
    if not d.is_dir():
        raise ValueError(f"unknown exercise: {exercise_id!r}")
    if len(code.encode("utf-8")) > MAX_CODE:
        return dict(
            passed=False,
            stdout="",
            error=f"El código supera {MAX_CODE // 1000} KB.",
            tests=[],
            ms=0,
            killed=None,
        )
    with tempfile.TemporaryDirectory(prefix="qg-") as work:
        main = Path(work) / "main.py"
        main.write_text(code, encoding="utf-8")
        report_r, report_w = os.pipe()
        env = job_env(work, os.environ.get("PATH", ""))
        env |= {
            "MPLCONFIGDIR": str(font_cache()),
            "QG_REPORT_FD": str(report_w),
            "QG_BLOCK": ",".join(block),
        }
        proc = subprocess.Popen(
            job_argv(mode, str(main), str(d / "check.py") if mode == "check" else None),
            cwd=work,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            pass_fds=(report_w,),
        )
        os.close(report_w)
        assert proc.stdout is not None
        over = threading.Event()
        out, report = bytearray(), bytearray()
        readers = [
            threading.Thread(target=drain, args=(proc.stdout.fileno(), OUT_BYTES, out, over)),
            threading.Thread(target=drain, args=(report_r, REPORT_CAP, report, over)),
        ]
        for t in readers:
            t.start()
        killed: str | None = None
        while proc.poll() is None and not killed:
            if over.is_set():
                killed = "output"
            elif time.monotonic() > start + timeout:
                killed = "time"
            else:
                time.sleep(POLL)
        with contextlib.suppress(OSError):
            os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        for t in readers:
            t.join(timeout=2)
        proc.stdout.close()
        os.close(report_r)
    why = killed and stopped(killed, timeout, 0, 0, OUT_BYTES)
    return result(
        mode,
        bytes(report),
        out.decode("utf-8", "replace"),
        killed,
        why,
        round((time.monotonic() - start) * 1000),
    )
