"""API used by the check.py files of exercises/.

    from qgcheck import learner, counts, visible

    @visible("n = 2, 3 y 4")
    def test_small():
        assert set(counts(learner.ghz(2))) == {"00", "11"}, "con n = 2 no salen solo 00 y 11"

Each `test_*` function is a case. With `@visible` the learner sees its name and its message; without
it the case is hidden: the learner sees only "caso oculto" and the `assert` message, so that message
must not reveal the case data. `@hint(2)` links the case to hint 2 of the exercise (the first is 1).
If the case fails, the learner sees that hint next to it. What the learner wrote is read with
`learner.<name>` inside the case, not when the file is imported. This module does not import qiskit
until a helper is called, so build.py can read the cases without it.

The learner's code runs in another process and only data travels: numbers, strings, lists, tuples,
dictionaries, bytes, NumPy arrays, `Statevector`, `Operator`, `SparsePauliOp` and `QuantumCircuit`.
A case that needs to pass the learner's code an object that is not data, or to use one it returns (a
class, a `PassManager`, a `Target`, matplotlib axes), does it in a check.py function marked
`@inside`. That function runs in the learner's process, reads `learner` from there and receives and
returns data. The case, outside, compares with the expected values:

    @inside
    def pairs(circuit):
        out = PassManager([learner.SwapACx()]).run(circuit)
        return out.count_ops()["swap"]
"""

import functools
import inspect
from collections import Counter
from collections.abc import Callable
from typing import Any, Protocol

from qgcheck.runner import grade as grade


class Names(Protocol):
    """The names the learner's code defined."""

    def __contains__(self, name: str, /) -> bool: ...

    def __getitem__(self, name: str, /) -> Any: ...


def visible(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Expose this case under the given name."""

    def mark(fn: Any) -> Any:
        fn.qg_visible = name
        return fn

    return mark


def hint(number: int) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Link this case to hint `number` (from 1) of the exercise's `hints`."""
    if isinstance(number, bool) or not isinstance(number, int) or number < 1:
        raise ValueError(f"hints are numbered from 1, not {number!r}")

    def mark(fn: Any) -> Any:
        fn.qg_hint = number
        return fn

    return mark


_remote: Callable[[str, tuple[Any, ...], dict[str, Any]], Any] | None = None


class LearnerError(Exception):
    """An exception the learner's code raised in another process."""


def inside(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Mark a check.py function that runs in the learner's process.

    Outside that process the call travels to it and returns the value.
    The arguments and the value must be serializable data.
    """

    @functools.wraps(fn)
    def call(*args: Any, **kwargs: Any) -> Any:
        if _remote is None:
            return fn(*args, **kwargs)
        return _remote(fn.__name__, args, kwargs)

    call.qg_inside = True  # type: ignore[attr-defined]
    return call


class HelperFailure(AssertionError):
    """A failure a qgcheck helper detects without knowing the case input."""


_last_use: dict[str, str | None] = {"name": None, "call": None}


def last_use() -> str | None:
    """How the learner's code was last used: `ghz(7)` or, if it was not a function, `MiBackend`."""
    return _last_use["call"] or (f"`{_last_use['name']}`" if _last_use["name"] else None)


def _note_use(text: str) -> None:
    _last_use["call"] = text


def _shown(value: Any) -> str:
    text = repr(value)
    if " at 0x" in text:
        return type(value).__name__
    return text if len(text) <= 40 else text[:37] + "..."


def _recorded(name: str, fn: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(fn)
    def call(*args: Any, **kwargs: Any) -> Any:
        shown = [*map(_shown, args), *(f"{k}={_shown(v)}" for k, v in kwargs.items())]
        _last_use["call"] = f"`{name}({', '.join(shown)})`"
        return fn(*args, **kwargs)

    return call


class _Learner:
    """Access to the names the learner's code defined."""

    def __init__(self) -> None:
        object.__setattr__(self, "_ns", None)

    def _bind(
        self,
        ns: Names | None,
        remote: Callable[[str, tuple[Any, ...], dict[str, Any]], Any] | None = None,
    ) -> None:
        global _remote
        _remote = remote
        object.__setattr__(self, "_ns", ns)
        _last_use.update(name=None, call=None)

    def __getattr__(self, name: str) -> Any:
        ns = object.__getattribute__(self, "_ns")
        if ns is None:
            raise RuntimeError("learner exists only while qgcheck grades a learner's code")
        if name not in ns:
            raise AssertionError(f"Falta definir `{name}` en tu código.")
        _last_use.update(name=name, call=None)
        value = ns[name]
        return _recorded(name, value) if inspect.isfunction(value) else value


learner = _Learner()


def _first_register(result: Any, what: str) -> Any:
    data = result[0].data
    names = list(data.keys())
    if not names:
        raise HelperFailure(f"{what} no mide ningún qubit: falta `measure_all()` o una medición.")
    return data[names[0]]


def counts(circuit: Any, shots: int = 1024, seed: int = 7) -> Any:
    """Return the counts of the first classical register using StatevectorSampler."""
    from qiskit.primitives import StatevectorSampler

    result = StatevectorSampler(seed=seed).run([circuit], shots=shots).result()
    return _first_register(result, "El circuito").get_counts()


def aer_counts(circuit: Any, shots: int = 512, seed: int = 11) -> Any:
    """Return the counts of the first classical register using SamplerV2."""
    from qiskit_aer.primitives import SamplerV2

    result = SamplerV2(seed=seed).run([circuit], shots=shots).result()
    return _first_register(result, "El circuito").get_counts()


def gates(circuit: Any) -> Counter[str]:
    """Count operations by name, including inside control-flow blocks."""
    found: Counter[str] = Counter()
    for inst in circuit.data:
        found[inst.operation.name] += 1
        for body in getattr(inst.operation, "blocks", ()):
            found.update(gates(body))
    return found


def state(circuit: Any) -> Any:
    """Return the circuit's statevector without final measurements."""
    from qiskit.quantum_info import Statevector

    return Statevector(circuit.remove_final_measurements(inplace=False))


def unsupported(circuit: Any, target: Any) -> list[str]:
    """List the circuit instructions the target does not allow where they are: ['h en 0', 'cz en 0-2']."""
    found: list[str] = []
    for inst in circuit.data:
        at = tuple(circuit.find_bit(q).index for q in inst.qubits)
        if not target.instruction_supported(inst.operation.name, at):
            found.append(f"{inst.operation.name} en {'-'.join(map(str, at))}")
    return found


def operator(circuit: Any) -> Any:
    """Return a circuit's operator over the virtual qubits of the original circuit.

    If the circuit is transpiled, it applies the initial and final layout so the result can be
    compared with the original's operator. It builds the matrix of only the qubits the circuit
    touches, so it works with a circuit transpiled to a 156-qubit chip.
    """
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Operator

    body = circuit.remove_final_measurements(inplace=False)
    layout = body.layout
    if layout is None:
        return Operator(body)
    first, last = layout.initial_index_layout(filter_ancillas=True), layout.final_index_layout()
    touched = {body.find_bit(q).index for inst in body.data for q in inst.qubits}
    used = sorted(touched | set(first) | set(last))
    at = {physical: k for k, physical in enumerate(used)}
    small = QuantumCircuit(len(used))
    for inst in body.data:
        small.append(inst.operation, [at[body.find_bit(q).index] for q in inst.qubits])
    n = len(first)

    def index(places: Any, x: int) -> int:
        return sum(((x >> v) & 1) << at[places[v]] for v in range(n))

    full = Operator(small).data
    rows = [index(last, y) for y in range(2**n)]
    cols = [index(first, x) for x in range(2**n)]
    return Operator(full[np.ix_(rows, cols)])
