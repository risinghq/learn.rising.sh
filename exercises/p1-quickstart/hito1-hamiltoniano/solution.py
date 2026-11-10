from qiskit.quantum_info import SparsePauliOp


def hamiltoniano(J, h):
    return SparsePauliOp.from_list([("ZZ", J), ("IX", h), ("XI", h)])
