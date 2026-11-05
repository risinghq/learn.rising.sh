from qiskit import QuantumCircuit
from qiskit.circuit.library import CXGate
from qiskit.quantum_info import Operator, Pauli


def variante(antes):
    """Una CX con la Pauli `antes` (una cadena como "XZ") antes y otra Pauli después."""
    qc = QuantumCircuit(2)
    qc.cx(0, 1)
    return qc


for etiqueta in ("IX", "ZI", "YY"):
    print(etiqueta, "→ equivale a una CX:", Operator(variante(etiqueta)).equiv(Operator(CXGate())))
