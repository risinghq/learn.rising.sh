from qiskit.circuit import Measure, Parameter
from qiskit.circuit.library import CZGate, RZGate, SXGate, XGate
from qiskit.transpiler import InstructionProperties, Target


def crear_target(pares):
    target = Target(num_qubits=3)
    theta = Parameter("θ")
    for puerta in (RZGate(theta), SXGate(), XGate()):
        target.add_instruction(puerta, {(q,): InstructionProperties(error=1e-4) for q in range(3)})
    # Añade Measure() en los tres qubits y la CZ solo en los pares dados.
    return target
