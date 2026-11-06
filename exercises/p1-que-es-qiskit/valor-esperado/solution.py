from qiskit.quantum_info import Statevector


def valor_esperado(qc, obs):
    return float(Statevector(qc).expectation_value(obs).real)
