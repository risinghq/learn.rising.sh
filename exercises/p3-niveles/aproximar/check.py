import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import UnitaryGate
from qiskit.quantum_info import Operator, average_gate_fidelity
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

from qgcheck import learner, operator, visible

BACKEND = FakeSherbrooke()


def circuit():
    azar = np.random.default_rng(8)
    q, _ = np.linalg.qr(azar.normal(size=(4, 4)) + 1j * azar.normal(size=(4, 4)))
    qc = QuantumCircuit(2)
    qc.append(UnitaryGate(q), range(2))
    qc.swap(0, 1)
    return qc


def transpiled(degree, seed=12345):
    return generate_preset_pass_manager(3, backend=BACKEND, approximation_degree=degree, seed_transpiler=seed).run(circuit())


@visible("el nivel 3 usa 2 ecr o menos")
def test_two_ecr():
    n = transpiled(learner.grado).count_ops().get("ecr", 0)
    assert n <= 2, f"Con grado = {learner.grado} salen {n} ecr."


def test_other_seeds():
    for seed in (1, 2, 3):
        n = transpiled(learner.grado, seed).count_ops().get("ecr", 0)
        assert n <= 2, f"Con seed = {seed} y grado = {learner.grado} salen {n} ecr."


def test_not_exact_but_not_too_loose():
    grado = learner.grado
    assert 0.9 <= grado < 1, f"`grado` vale {grado}, fuera del intervalo permitido."


def test_the_circuit_is_still_close():
    grado = learner.grado
    fidelity = average_gate_fidelity(operator(transpiled(grado)), Operator(circuit()))
    assert fidelity > 0.9, f"Con grado = {grado}, la fidelidad media de la puerta es {fidelity:.3f}: aproximaste demasiado."
