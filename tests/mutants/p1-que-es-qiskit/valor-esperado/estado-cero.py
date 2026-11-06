from qiskit.quantum_info import Statevector


def valor_esperado(qc, obs):
    return float(Statevector.from_label("0" * qc.num_qubits).expectation_value(obs).real)
