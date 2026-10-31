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
from pathlib import Path  # noqa: E402
from typing import Any, cast  # noqa: E402

from qgcheck import learner, spec  # noqa: E402
from qgcheck.cases import REPLY_KEYS, Channel, Names, run_cases  # noqa: E402
from qgcheck.host import serve  # noqa: E402
from qgcheck.source import CODE_NAME, describe, preload  # noqa: E402
from qgcheck.wire import WireError, receive, send  # noqa: E402

# BLAS and matplotlib threads make Python warn on every fork, and the warning would reach the
# learner's output.
warnings.filterwarnings("ignore", message=".*multi-threaded.*fork", category=DeprecationWarning)

PR_SET_DUMPABLE = 4


class Host(Channel):
    """Client of the learner's process."""

    def __init__(self, code_path: str, check_path: str) -> None:
        super().__init__()
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

    def stop(self) -> None:
        self._sock.close()
        os.kill(self._pid, 9)
        os.waitpid(self._pid, 0)

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
        return {"error": None, "tests": run_cases(spec.load_cases(Path(check_path)))}
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
