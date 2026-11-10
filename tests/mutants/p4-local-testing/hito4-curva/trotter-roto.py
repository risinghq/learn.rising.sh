import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector
from scipy.linalg import expm


def curvas(n, J, h, dt, pasos):
    terminos = [("ZZ", [i, i + 1], J) for i in range(n - 1)] + [("X", [i], h) for i in range(n)]
    H = SparsePauliOp.from_sparse_list(terminos, num_qubits=n).to_matrix()
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    U = expm(-1j * dt * H)
    psi = Statevector.from_label("0" * n)
    exacta = []
    for _ in range(pasos + 1):
        exacta.append(float(psi.expectation_value(M).real))
        psi = psi.evolve(U)
    qc = QuantumCircuit(n)
    trotter = [1.0]
    for _ in range(pasos):
        for i in range(n):
            qc.rx(2 * h * dt, i)
        trotter.append(float(Statevector(qc).expectation_value(M).real))
    return exacta, trotter
