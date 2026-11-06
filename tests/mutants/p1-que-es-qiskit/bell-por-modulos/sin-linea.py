from qiskit import QuantumCircuit
from qiskit.circuit.library import CXGate, HGate
from qiskit.quantum_info import Statevector
from qiskit.transpiler import generate_preset_pass_manager


def bell():
    qc = QuantumCircuit(2)
    qc.append(HGate(), [0])
    qc.append(CXGate(), [0, 1])
    return qc


def probabilidades(qc):
    return dict(Statevector(qc).probabilities_dict())


def a_base(qc):
    pm = generate_preset_pass_manager(optimization_level=1, basis_gates=["rz", "sx", "cz"])
    return pm.run(qc)
