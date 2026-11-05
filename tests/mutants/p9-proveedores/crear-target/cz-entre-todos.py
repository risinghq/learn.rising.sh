from itertools import combinations

from qiskit.circuit import Measure, Parameter
from qiskit.circuit.library import CZGate, RZGate, SXGate, XGate
from qiskit.transpiler import InstructionProperties, Target


def crear_target(pares):
    target = Target(num_qubits=3)
    theta = Parameter("θ")
    for puerta in (RZGate(theta), SXGate(), XGate(), Measure()):
        target.add_instruction(puerta, {(q,): InstructionProperties(error=1e-4) for q in range(3)})
    target.add_instruction(
        CZGate(), {par: InstructionProperties(error=1e-2) for par in combinations(range(3), 2)}
    )
    return target
