import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector
from scipy.linalg import expm


def hamiltoniano(n, J, h):
    terminos = [("ZZ", [i, i + 1], J) for i in range(n - 1)] + [("X", [i], h) for i in range(n)]
    return SparsePauliOp.from_sparse_list(terminos, num_qubits=n)


def magnetizacion(n):
    return SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)


def curvas(n, J, h, dt, pasos):
    M = magnetizacion(n)
    U = expm(-1j * dt * hamiltoniano(n, J, h).to_matrix())
    psi = Statevector.from_label("0" * n)
    exacta = []
    for _ in range(pasos + 1):
        exacta.append(float(psi.expectation_value(M).real))
        psi = psi.evolve(U)

    qc = QuantumCircuit(n)
    trotter = [1.0]
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
        trotter.append(float(Statevector(qc).expectation_value(M).real))
    return exacta, trotter
