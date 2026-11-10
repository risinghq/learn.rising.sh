from qiskit.quantum_info import SparsePauliOp


def hamiltoniano(n, J, h):
    terminos = [("ZZ", [0, i + 1], J) for i in range(n - 1)]
    terminos += [("X", [i], h) for i in range(n)]
    return SparsePauliOp.from_sparse_list(terminos, num_qubits=n)
