"""A job process: run the learner's code or check it against an exercise.

    python -u -P -m qgcheck.job run CODE
    python -u -P -m qgcheck.job check CODE CHECK.PY

Write to the QG_REPORT_FD descriptor a JSON `{"error": text or null, "tests": [...]}` with the
shape `qgcheck.grade` gives those fields. `QG_BLOCK` lists, comma-separated, modules that cannot be
imported.

`run` runs the code in this process. `check` imports the libraries the code and the cases use,
forks the learner's process (`qgcheck.host`) with them already loaded and runs the cases of
`check.py` here. `qgcheck.learner` binds to a namespace whose functions are calls to that process,
so the learner's code never shares a process, channel or state with the cases. Only data travels
between processes (`qgcheck.wire`).
"""

import sys

# Qiskit Runtime and Mitigation load scipy and their clients on import, and almost no case uses
# them. With `all` and no filter, Qiskit fails (`n_local` has no `__all__`).
LAZY_IMPORTERS = ("qiskit_ibm_runtime", "qiskit_mitigation")


def _lazy(importer: str | None, name: str, fromlist: tuple[str, ...] | None) -> bool:
    return importer is not None and importer.startswith(LAZY_IMPORTERS)


sys.set_lazy_imports_filter(_lazy)
sys.set_lazy_imports("all")

import ctypes  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import secrets  # noqa: E402
import socket  # noqa: E402
import traceback  # noqa: E402
import warnings  # noqa: E402
from collections.abc import Callable, Sequence  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any, cast  # noqa: E402

from qgcheck import HelperFailure, LearnerError, _note_use, last_use, learner, spec  # noqa: E402
from qgcheck.host import serve  # noqa: E402
from qgcheck.source import CODE_NAME, describe, preload  # noqa: E402
from qgcheck.wire import BROKEN, WireError, decode, encode, receive, send  # noqa: E402

# BLAS and matplotlib threads make Python warn on every fork, and the warning would reach the
# learner's output.
warnings.filterwarnings("ignore", message=".*multi-threaded.*fork", category=DeprecationWarning)

PR_SET_DUMPABLE = 4
REPLY_KEYS = {"id", "value", "raised", "error", "used"}


class Host:
    """Client of the learner's process."""

    def __init__(self, code_path: str, check_path: str) -> None:
        self._sock, theirs = socket.socketpair()
        self._pid = os.fork()
        if self._pid == 0:
            try:
                self._sock.close()
                serve(theirs, code_path, check_path)
            except BaseException:
                traceback.print_exc()
            finally:
                os._exit(0)
        theirs.close()
        self._broken = False

    def stop(self) -> None:
        self._sock.close()
        os.kill(self._pid, 9)
        os.waitpid(self._pid, 0)

    def request(
        self,
        op: str,
        name: str | None = None,
        args: Sequence[Any] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        """Return the request's value; a learner failure is raised as it would be in the case."""
        if self._broken:
            raise AssertionError(BROKEN)
        try:
            reply = self._exchange(
                {
                    "op": op,
                    "name": name,
                    "args": encode(list(args)),
                    "kwargs": encode(kwargs or {}),
                }
            )
            if isinstance(reply.get("used"), str):
                _note_use(reply["used"])
            if "error" in reply:
                raise AssertionError(str(reply["error"]))
            if "raised" in reply:
                kind, text = reply["raised"]
                if kind == "AssertionError":
                    raise AssertionError(str(text))
                raise LearnerError(f"{kind}: {text}")
            return self._decode(reply["value"])
        except AssertionError, LearnerError:
            raise
        except WireError, KeyError, TypeError, ValueError, RecursionError, ImportError, OSError:
            self._broken = True
            raise AssertionError(BROKEN) from None

    def _decode(self, value: Any) -> Any:
        """A learner datum that cannot be rebuilt (e.g. a `Statevector` whose dimensions do not
        match, which raises `QiskitError`) is a broken channel, not an exception of their code."""
        try:
            return decode(value)
        except Exception:
            self._broken = True
            raise AssertionError(BROKEN) from None

    def _exchange(self, message: dict[str, Any]) -> dict[str, Any]:
        """Send the request with an `id` the learner cannot guess and read its reply.

        The learner's process does not know the `id` before receiving the request, so it cannot
        leave written replies that this side would take for those of future requests.
        """
        ident = secrets.token_hex(16)
        send(self._sock.fileno(), message | {"id": ident})
        reply = receive(self._sock.fileno())
        valid = (
            reply.get("id") == ident
            and len(reply.keys() & {"value", "raised", "error"}) == 1
            and reply.keys() <= REPLY_KEYS
        )
        if not valid:
            raise WireError("invalid reply")
        return reply


class Names:
    """The namespace `qgcheck.learner` reads.

    `kinds` says which names the learner defined and which are functions or classes. A function is
    a call to the learner's process; the value of any other name is requested once.
    """

    def __init__(self, host: Host, kinds: Any) -> None:
        if not (
            isinstance(kinds, dict)
            and all(isinstance(k, str) and isinstance(v, bool) for k, v in kinds.items())
        ):
            raise AssertionError(BROKEN)
        self._host, self._kinds = host, kinds
        self._values: dict[str, Any] = {}

    def __contains__(self, name: str) -> bool:
        return name in self._kinds

    def __getitem__(self, name: str) -> Any:
        if self._kinds[name]:

            def call(*args: Any, **kwargs: Any) -> Any:
                return self._host.request("call", name, args, kwargs)

            return call
        if name not in self._values:
            self._values[name] = self._host.request("get", name)
        return self._values[name]


def run_case(fn: Callable[[], object]) -> str | None:
    try:
        fn()
    except HelperFailure as exc:
        return f"{exc} Pasó al usar {last_use()}." if last_use() else str(exc)
    except AssertionError as exc:
        return str(exc) or "El caso falló."
    except Exception as exc:
        what = str(exc) if isinstance(exc, LearnerError) else f"{type(exc).__name__}: {exc}"
        return f"Tu código lanzó {what}" + (f" Pasó al usar {last_use()}." if last_use() else "")
    return None


def run_cases(check_path: str) -> list[dict[str, Any]]:
    tests: list[dict[str, Any]] = []
    hidden = 0
    for fn, shown in spec.load_cases(Path(check_path)):
        message = run_case(fn)
        if shown is None:
            hidden += 1
        tests.append(
            dict(
                name=shown or f"caso oculto {hidden}",
                visible=shown is not None,
                passed=message is None,
                message=message,
                hint=getattr(fn, "qg_hint", None),
            )
        )
    return tests


def run(code_path: str) -> dict[str, Any]:
    source = Path(code_path).read_text(encoding="utf-8")
    try:
        exec(compile(source, CODE_NAME, "exec"), {"__name__": "__main__"})
    except BaseException as e:
        return {"error": describe(e, source), "tests": []}
    return {"error": None, "tests": []}


def check(code_path: str, check_path: str) -> dict[str, Any]:
    # Same uid as the learner: without this they could read or write this process's memory. The
    # learner's processes inherit the flag.
    ctypes.CDLL(None).prctl(PR_SET_DUMPABLE, 0, 0, 0, 0)
    preload(
        Path(code_path).read_text(encoding="utf-8"), Path(check_path).read_text(encoding="utf-8")
    )
    host = Host(code_path, check_path)
    try:
        try:
            names = Names(host, host.request("names"))
        except AssertionError as e:
            return {"error": str(e), "tests": []}
        learner._bind(
            names, remote=lambda name, args, kwargs: host.request("inside", name, args, kwargs)
        )
        return {"error": None, "tests": run_cases(check_path)}
    finally:
        host.stop()


def main(mode: str, code_path: str, check_path: str = "") -> None:
    for name in filter(None, os.environ.get("QG_BLOCK", "").split(",")):
        cast("dict[str, Any]", sys.modules)[name] = None
    report = check(code_path, check_path) if mode == "check" else run(code_path)
    with os.fdopen(int(os.environ["QG_REPORT_FD"]), "w") as f:
        json.dump(report, f)
    if mode == "check":
        # The checker has nothing to close; shutting down the interpreter with Qiskit loaded costs 0.1 s.
        sys.stdout.flush()
        os._exit(0)


if __name__ == "__main__":
    main(*sys.argv[1:])
