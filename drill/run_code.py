"""Runs the programs of the authored drill items: reads a JSON list of
{"lang", "source"} on stdin and writes the Qiskit version and one outcome per
program on stdout. Python programs run with a fresh namespace and their
output is what they print. QASM 2 programs are loaded into a circuit and
their output is its text drawing."""

import contextlib
import io
import json
import signal
import sys
import traceback
from types import FrameType

import qiskit
from qiskit import qasm2

LIMIT_SECONDS = 20


def run_python(source: str) -> str:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        exec(compile(source, "<item>", "exec"), {"__name__": "__drill__"})
    return out.getvalue()


def run_qasm(source: str) -> str:
    return str(qasm2.loads(source).draw(output="text"))


def on_alarm(_signal: int, _frame: FrameType | None) -> None:
    raise TimeoutError(f"more than {LIMIT_SECONDS} s")


def outcome(program: dict[str, str]) -> dict[str, object]:
    signal.alarm(LIMIT_SECONDS)
    try:
        run = run_qasm if program["lang"] == "qasm" else run_python
        return {"ok": True, "out": run(program["source"]), "error": ""}
    except BaseException as error:
        last = traceback.format_exception_only(type(error), error)[-1].strip()
        return {"ok": False, "out": "", "error": last}
    finally:
        signal.alarm(0)


def main() -> None:
    signal.signal(signal.SIGALRM, on_alarm)
    programs: list[dict[str, str]] = json.load(sys.stdin)
    results = [outcome(program) for program in programs]
    json.dump({"qiskit": qiskit.__version__, "results": results}, sys.stdout)


if __name__ == "__main__":
    main()
