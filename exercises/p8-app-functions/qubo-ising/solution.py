import ast

from qiskit.quantum_info import SparsePauliOp


def qubo_a_ising(qubo, n):
    constante = 0.0
    pesos = {}
    for clave, coeficiente in qubo.items():
        qubits = ast.literal_eval(clave)
        if len(qubits) == 0:
            constante += coeficiente
        elif len(qubits) == 1:
            (i,) = qubits
            constante += coeficiente / 2
            pesos[(i,)] = pesos.get((i,), 0) - coeficiente / 2
        else:
            i, j = qubits
            constante += coeficiente / 4
            pesos[(i,)] = pesos.get((i,), 0) - coeficiente / 4
            pesos[(j,)] = pesos.get((j,), 0) - coeficiente / 4
            pesos[(i, j)] = pesos.get((i, j), 0) + coeficiente / 4
    terms = [("Z" * len(q), list(q), float(weight)) for q, weight in pesos.items()]
    hamiltoniano = SparsePauliOp.from_sparse_list(terms or [("I", [0], 0.0)], num_qubits=n)
    return hamiltoniano, constante
