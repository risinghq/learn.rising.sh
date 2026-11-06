from qiskit.quantum_info import SparsePauliOp, Statevector


def valor_esperado(qc, obs):
    estado = Statevector(qc)
    return float(sum(estado.expectation_value(SparsePauliOp(p)).real for p in obs.paulis))
