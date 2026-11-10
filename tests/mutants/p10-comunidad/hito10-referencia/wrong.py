import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector
from scipy.linalg import expm


def trotter(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(h * dt, i)
    return qc


def curvas(n, J, h, T, pasos):
    dt = T / pasos
    H = SparsePauliOp.from_sparse_list(
        [("ZZ", [i, i + 1], J) for i in range(n - 1)] + [("X", [i], h) for i in range(n)], num_qubits=n
    ).to_matrix()
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    psi0 = np.zeros(2**n, dtype=complex)
    psi0[0] = 1
    exacta = []
    for k in range(pasos + 1):
        psi = expm(-1j * H * k * dt) @ psi0
        exacta.append(float(np.real(np.vdot(psi, M.to_matrix() @ psi))))
    trot = [float(np.real(Statevector(trotter(n, J, h, dt, k)).expectation_value(M))) for k in range(pasos + 1)]
    return exacta, trot
