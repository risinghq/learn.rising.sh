import functools

from qiskit import QuantumCircuit
from qiskit.circuit.random import random_circuit
from qiskit.transpiler import CouplingMap, generate_preset_pass_manager

from qgcheck import inside, learner, visible

GRID = CouplingMap.from_grid(3, 3)


def transpile_with(qc, seed):
    return generate_preset_pass_manager(1, coupling_map=GRID, basis_gates=["cx", "rz", "sx", "x"], seed_transpiler=seed).run(qc)


@inside
def chosen(qc, seeds, kind="list"):
    """Devuelve el circuito de `mejor_de` o el tipo de su resultado.

    `kind` da la forma de las semillas: `list`, `range` (`seeds` son los argumentos de `range`) o
    `generator`.
    """
    given = {"list": list, "range": lambda s: range(*s), "generator": lambda s: (k for k in s)}[
        kind
    ](seeds)
    out = learner.mejor_de(qc, given)
    return (out, None) if isinstance(out, QuantumCircuit) else (None, type(out).__name__)


def chosen_cx(qc, seeds, kind="list"):
    """Devuelve las `cx` del circuito elegido, o `None` si no devolvió un circuito."""
    circuit, _ = chosen(qc, seeds, kind)
    return None if circuit is None else cx(circuit)


def cx(circuit):
    return circuit.count_ops().get("cx", 0)


def random_9(seed):
    return random_circuit(9, 6, max_operands=2, seed=seed)


# The cases ask for the same circuits and seeds, so each reference transpile runs once.
@functools.cache
def cx_with_seed(circuit_seed, seed):
    return cx(transpile_with(random_9(circuit_seed), seed))


def best_cx(circuit_seed, seeds):
    return min(cx_with_seed(circuit_seed, seed) for seed in seeds)


@visible("devuelve un circuito transpilado")
def test_returns_a_circuit():
    circuit, other = chosen(random_9(7), [0, 1], "range")
    assert circuit is not None, f"`mejor_de` devuelve {other}; debe devolver un `QuantumCircuit`."


@visible("el circuito elegido tiene el mínimo de cx de las diez semillas")
def test_best_of_ten():
    got = chosen_cx(random_9(7), [0, 10], "range")
    assert got == best_cx(7, range(10)), f"Con semillas = range(10), el circuito elegido tiene {got} cx."


def test_other_circuit():
    got = chosen_cx(random_9(3), [0, 5], "range")
    assert got == best_cx(3, range(5)), f"Con otro circuito, el elegido por `mejor_de` tiene {got} cx."


def test_only_the_given_seeds():
    seeds = [3, 0, 1]
    got = chosen_cx(random_9(7), seeds)
    assert got == best_cx(7, seeds), f"Con semillas = {seeds}, el circuito elegido tiene {got} cx."


def test_accepts_a_generator():
    got = chosen_cx(random_9(7), list(range(6)), "generator")
    assert got == best_cx(7, range(6)), f"Con semillas = un generador de 0 a 5, el elegido tiene {got} cx."
