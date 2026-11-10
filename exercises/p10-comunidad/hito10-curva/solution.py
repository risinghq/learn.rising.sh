import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit_ibm_runtime.fake_provider import FakeFez
from scipy.linalg import expm

FEZ = FakeFez()


def trotter(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
    return qc


def evaluar(n, J, h, T, pasos):
    dt = T / pasos
    H = SparsePauliOp.from_sparse_list(
        [("ZZ", [i, i + 1], J) for i in range(n - 1)] + [("X", [i], h) for i in range(n)], num_qubits=n
    ).to_matrix()
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    psi0 = np.zeros(2**n, dtype=complex)
    psi0[0] = 1
    error = 0.0
    for k in range(pasos + 1):
        psi = expm(-1j * H * k * dt) @ psi0
        exacta = float(np.real(np.vdot(psi, M.to_matrix() @ psi)))
        error = max(error, abs(exacta - float(np.real(Statevector(trotter(n, J, h, dt, k)).expectation_value(M)))))
    qc = trotter(n, J, h, dt, pasos)
    qc.measure_all()
    return error, transpile(qc, FEZ, optimization_level=1, seed_transpiler=7).depth()


def elegir_pasos(n, J, h, T):
    for pasos in range(1, 21):
        error, profundidad = evaluar(n, J, h, T, pasos)
        if error < 0.02 and profundidad <= 200:
            return pasos
    return 0
