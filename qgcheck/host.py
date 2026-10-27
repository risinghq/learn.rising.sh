"""Run the learner's code and serve requests over a socket.

The process keeps the learner's state between requests. It cannot fork per
request because the learner may have created threads.
"""

import contextlib
import inspect
import os
import socket
from pathlib import Path
from typing import Any

from qgcheck import last_use, learner, spec
from qgcheck.source import CODE_NAME, describe, uses_inside
from qgcheck.wire import BROKEN, WireError, decode, encode, receive, send

MESSAGE_CAP = 300


def failure(text: str) -> dict[str, Any]:
    return {"error": text[:MESSAGE_CAP]}


def is_function(value: Any) -> bool:
    return inspect.isroutine(value) or inspect.isclass(value)


def answer(namespace: dict[str, Any], check: Any, request: dict[str, Any]) -> dict[str, Any]:
    op, name = request.get("op"), request.get("name")
    if op == "names":
        return {
            "value": encode(
                {n: is_function(v) for n, v in namespace.items() if not n.startswith("__")}
            )
        }
    if op == "inside":
        target = getattr(check, str(name), None)
        if not getattr(target, "qg_inside", False):
            return failure(BROKEN)
        return run(target, name, request, with_use=True)
    if name not in namespace:
        return failure(f"Falta definir `{name}` en tu código.")
    value = namespace[name]
    if op == "call":
        if not callable(value):
            return failure(f"`{name}` debe ser una función.")
        return run(value, name, request)
    return encoded(value, name)


def run(fn: Any, name: Any, request: dict[str, Any], with_use: bool = False) -> dict[str, Any]:
    try:
        value = fn(*decode(request.get("args", [])), **decode(request.get("kwargs", {})))
    except Exception as e:
        reply: dict[str, Any] = {"raised": [type(e).__name__, str(e)[:MESSAGE_CAP]]}
    else:
        reply = encoded(value, name)
    if with_use:
        reply["used"] = last_use()
    return reply


def encoded(value: Any, name: Any) -> dict[str, Any]:
    try:
        return {"value": encode(value)}
    except TypeError as e:
        return failure(f"`{name}` contiene {e} que no se puede comprobar.")


def serve(sock: socket.socket, code_path: str, check_path: str) -> None:
    sock_fd = sock.fileno()
    # Closing only the inherited descriptors avoids the cost of walking a huge range.
    for fd in sorted(int(name) for name in os.listdir("/proc/self/fd")):
        if fd > 2 and fd != sock_fd:
            with contextlib.suppress(OSError):
                os.close(fd)
    source = Path(code_path).read_text(encoding="utf-8")
    namespace: dict[str, Any] = {"__name__": "__main__"}
    error: str | None = None
    check: Any = None
    try:
        exec(compile(source, CODE_NAME, "exec"), namespace)
    except BaseException as e:
        error = describe(e, source)
    else:
        learner._bind(namespace)
        # Importing check.py repeats its constants in this process: only done when it needs it.
        if check_path and uses_inside(Path(check_path).read_text(encoding="utf-8")):
            check = spec.load_module(Path(check_path))
    while True:
        try:
            request = receive(sock_fd)
        except WireError:
            return
        reply = failure(error) if error is not None else answer(namespace, check, request)
        try:
            send(sock_fd, reply | {"id": request.get("id")})
        except WireError:
            # A reply that is too large must not leave the checker waiting.
            with contextlib.suppress(WireError):
                send(sock_fd, failure(BROKEN) | {"id": request.get("id")})
