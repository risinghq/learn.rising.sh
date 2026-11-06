from qiskit.quantum_info import SparsePauliOp


def z_del_qubit_0(n):
    return SparsePauliOp("I" * (n - 1) + "Z")
