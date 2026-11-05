from qiskit.quantum_info import SparsePauliOp


def resumen_observable(terminos):
    obs = SparsePauliOp.from_sparse_list(terminos, num_qubits=100)
    return (obs.num_qubits, len(obs))
