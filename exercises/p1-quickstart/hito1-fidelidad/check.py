import numpy as np
from qiskit.quantum_info import SparsePauliOp
from scipy.linalg import expm

from qgcheck import learner, visible


def expected(J, h, dt):
    H = SparsePauliOp.from_list([("ZZ", J), ("IX", h), ("XI", h)])
    exacto = expm(-1j * H.to_matrix() * dt) @ np.array([1, 0, 0, 0])
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(2)
    qc.rzz(2 * J * dt, 0, 1)
    qc.rx(2 * h * dt, 0)
    qc.rx(2 * h * dt, 1)
    from qiskit.quantum_info import Statevector
    return abs(np.vdot(exacto, Statevector.from_instruction(qc).data)) ** 2


@visible("la fidelidad coincide con la evolución exacta")
def test_default():
    got = learner.fidelidad(1.0, 0.5, 0.1)
    assert abs(got - expected(1.0, 0.5, 0.1)) < 1e-9, f"Con J = 1.0, h = 0.5 y dt = 0.1, `fidelidad` devuelve {got:.8f}."


def test_other_dt():
    got = learner.fidelidad(0.8, 1.1, 0.3)
    assert abs(got - expected(0.8, 1.1, 0.3)) < 1e-9, f"Con dt = 0.3, `fidelidad` devuelve {got} (formato corto: {got:.8f})."
