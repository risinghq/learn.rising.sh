from qiskit.quantum_info import SparsePauliOp


def etiquetas(terminos, n):
    obs = SparsePauliOp.from_sparse_list(terminos, num_qubits=n)
    return {
        etiqueta: float(coef.real) for etiqueta, coef in zip(obs.paulis.to_labels(), obs.coeffs)
    }
