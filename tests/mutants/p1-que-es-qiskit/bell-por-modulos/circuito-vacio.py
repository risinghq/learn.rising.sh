from qiskit import QuantumCircuit
from qiskit.circuit.library import CXGate, HGate
from qiskit.quantum_info import Statevector


def bell():
    qc = QuantumCircuit(2)
    qc.append(HGate(), [0])
    qc.append(CXGate(), [0, 1])
    return qc


def probabilidades(qc):
    return dict(Statevector(qc).probabilities_dict())


def a_base(qc):
    salida = QuantumCircuit(qc.num_qubits, qc.num_clbits)
    for k in range(qc.num_qubits):
        salida.sx(k)
    for k in range(qc.num_qubits - 1):
        salida.cz(k, k + 1)
    return salida
