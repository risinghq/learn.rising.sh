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
    exacta = []  # ✏️ ⟨M⟩ en t = 0, dt, …, pasos·dt con la evolución exacta desde |0…0⟩

    qc = QuantumCircuit(n)
    trotter = [1.0]
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
        trotter.append(float(Statevector(qc).expectation_value(M).real))
    return exacta, trotter
