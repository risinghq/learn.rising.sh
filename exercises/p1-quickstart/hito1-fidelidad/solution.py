import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector
from scipy.linalg import expm


def fidelidad(J, h, dt):
    H = SparsePauliOp.from_list([("ZZ", J), ("IX", h), ("XI", h)])
    qc = QuantumCircuit(2)
    qc.rzz(2 * J * dt, 0, 1)
    qc.rx(2 * h * dt, 0)
    qc.rx(2 * h * dt, 1)
    exacto = expm(-1j * H.to_matrix() * dt) @ np.array([1, 0, 0, 0])
    trotter = Statevector.from_instruction(qc).data
    return float(abs(np.vdot(exacto, trotter)) ** 2)
