from qiskit.quantum_info import SparsePauliOp


def qubo_a_ising(qubo, n):
    return SparsePauliOp.from_list([("I" * n, 0.0)]), 0.0
