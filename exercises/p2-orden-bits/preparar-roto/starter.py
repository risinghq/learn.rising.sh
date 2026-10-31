from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector


def preparar(k, n):
    qc = QuantumCircuit(n)
    bits = format(k, f"0{n}b")
    for qubit, bit in enumerate(bits):
        if bit == "1":
            qc.x(qubit)
    return qc


print(Statevector(preparar(5, 4)).probabilities().round(2))
