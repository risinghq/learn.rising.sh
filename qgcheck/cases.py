"""Run the cases of a check.py against a learner's code, whichever way the code is reached.

`Channel` is what a case's `learner.<name>` talks to. It sends a request to wherever the code runs
and returns the value, or fails as the case would. The server's job reaches the learner's process
over a socket (`qgcheck.job.Host`); the browser calls the code in its own interpreter
(`qgcheck.browser.LocalHost`). Both go through `qgcheck.wire`, so a value that is not data fails
the same way in both, and a message shows the same text.
"""

from collections.abc import Callable, Sequence
from typing import Any

from qgcheck import HelperFailure, LearnerError, _note_use, last_use
from qgcheck.wire import BROKEN, WireError, decode, encode

REPLY_KEYS = {"id", "value", "raised", "error", "used"}


class Channel:
    """Client of the learner's code."""

    def __init__(self) -> None:
        self._broken = False

    def _exchange(self, message: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

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


class Names:
    """The namespace `qgcheck.learner` reads.

    `kinds` says which names the learner defined and which are functions or classes. A function is
    a call to the learner's code; the value of any other name is requested once.
    """

    def __init__(self, host: Channel, kinds: Any) -> None:
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


def run_cases(cases: Sequence[tuple[Callable[..., Any], str | None]]) -> list[dict[str, Any]]:
    """Run each case of `spec.load_cases` and report it as `qgcheck.grade` does."""
    tests: list[dict[str, Any]] = []
    hidden = 0
    for fn, shown in cases:
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
