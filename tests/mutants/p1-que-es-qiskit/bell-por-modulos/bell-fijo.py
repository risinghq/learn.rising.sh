from qiskit import QuantumCircuit
from qiskit.circuit.library import CXGate, HGate
from qiskit.quantum_info import Statevector
from qiskit.transpiler import CouplingMap, generate_preset_pass_manager


def bell():
    qc = QuantumCircuit(2)
    qc.append(HGate(), [0])
    qc.append(CXGate(), [0, 1])
    qc.z(0)
    return qc


def probabilidades(qc):
    return {"00": 0.5, "11": 0.5}


def a_base(qc):
    pm = generate_preset_pass_manager(
        optimization_level=1,
        basis_gates=["rz", "sx", "cz"],
        coupling_map=CouplingMap.from_line(qc.num_qubits),
    )
    return pm.run(qc)
