import numpy as np
from scipy.linalg import expm
from qiskit.quantum_info import SparsePauliOp


def curva_ideal(n, J, h, dt, pasos):
    terms = [("ZZ", [i, i + 1], J) for i in range(n - 1)]
    terms += [("X", [i], h) for i in range(n)]
    hamiltoniano = SparsePauliOp.from_sparse_list(terms, num_qubits=n).to_matrix()
    magnetizacion = SparsePauliOp.from_sparse_list(
        [("Z", [i], 1 / n) for i in range(n)], num_qubits=n
    ).to_matrix()
    evolucion = expm(-1j * hamiltoniano * dt)
    estado = np.zeros(2**n, dtype=complex)
    estado[0] = 1
    valores = []
    for _ in range(pasos + 1):
        valores.append(float(np.real(np.vdot(estado, magnetizacion @ estado))))
        estado = evolucion @ estado
    return valores
