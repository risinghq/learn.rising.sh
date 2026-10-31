"""Grade a learner's code in this interpreter, for a browser that runs Pyodide.

    from qgcheck.browser import grade
    grade(code, check_source, "check")

It gives `qgcheck.grade`'s result, with the same cases, messages and checks: the code runs in this
process and a case reaches it through the same `qgcheck.wire` as the server's job does. A Web
Worker owns the interpreter, so the page stops a code that does not end by ending the worker, and
`killed` is only ever `output` here. A check.py that uses `@inside` needs a second process and cannot be
graded here.
"""

import contextlib
import io
import json
import types
from typing import Any

from qgcheck import learner, spec
from qgcheck.cases import Channel, Names, run_cases
from qgcheck.host import answer
from qgcheck.source import CODE_NAME, describe, stopped, uses_inside
from qgcheck.wire import BROKEN

OUT_BYTES = 64 * 1024


class TooMuchOutput(BaseException):
    """Raised in the learner's code that prints past the cap, so that it stops as in the runner."""


class Output(io.StringIO):
    def __init__(self) -> None:
        super().__init__()
        self._bytes = 0

    def write(self, text: str, /) -> int:
        data = text.encode("utf-8")
        room = OUT_BYTES - self._bytes
        if len(data) > room:
            super().write(data[:room].decode("utf-8", "ignore"))
            self._bytes = OUT_BYTES
            raise TooMuchOutput
        self._bytes += len(data)
        return super().write(text)


class LocalHost(Channel):
    """The learner's names, answered by the server's own `qgcheck.host.answer`."""

    def __init__(self, namespace: dict[str, Any]) -> None:
        super().__init__()
        self._namespace = namespace

    def _exchange(self, message: dict[str, Any]) -> dict[str, Any]:
        return answer(self._namespace, None, message)


def check(namespace: dict[str, Any], check_source: str) -> list[dict[str, Any]]:
    module = types.ModuleType("check")
    exec(compile(check_source, "check.py", "exec"), module.__dict__)
    host = LocalHost(namespace)
    learner._bind(Names(host, host.request("names")))
    try:
        return run_cases(spec.cases_of(module))
    finally:
        learner._bind(None)


def grade(code: str, check_source: str, mode: str) -> dict[str, Any]:
    if mode not in ("run", "check"):
        raise ValueError(f"invalid mode: {mode!r}")
    if mode == "check" and uses_inside(check_source):
        raise ValueError("a check.py with @inside needs the learner's own process")
    out = Output()
    error: str | None = None
    killed: str | None = None
    tests: list[dict[str, Any]] = []
    namespace: dict[str, Any] = {"__name__": "__main__"}
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        try:
            try:
                exec(compile(code, CODE_NAME, "exec"), namespace)
            except TooMuchOutput:
                raise
            except BaseException as exc:
                error = describe(exc, code)
            else:
                if mode == "check":
                    try:
                        tests = check(namespace, check_source)
                    except AssertionError as exc:
                        # The learner's code broke the channel before a case ran.
                        error = str(exc) or BROKEN
        except TooMuchOutput:
            killed, error, tests = "output", stopped("output", 0, 0, 0, OUT_BYTES), []
    return {
        "passed": error is None
        and (mode == "run" or (bool(tests) and all(t["passed"] for t in tests))),
        "stdout": out.getvalue(),
        "error": error,
        "tests": tests,
        "killed": killed,
    }


def grade_json(code: str, check_source: str, mode: str) -> str:
    """`grade` as JSON text, which is what the page's worker reads."""
    return json.dumps(grade(code, check_source, mode), ensure_ascii=False)
