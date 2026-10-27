# Wrong: adds an H to the Target.
from qiskit.circuit import Measure, Parameter
from qiskit.circuit.library import CZGate, HGate, RZGate, SXGate, XGate
from qiskit.transpiler import InstructionProperties, Target


def cadena(n):
    target = Target(f"cadena de {n}", num_qubits=n)
    target.add_instruction(RZGate(Parameter("t")), {(q,): None for q in range(n)})
    for puerta in (XGate(), SXGate(), Measure(), HGate()):
        target.add_instruction(puerta, {(q,): None for q in range(n)})
    target.add_instruction(CZGate(), {(k, k + 1): InstructionProperties(error=5e-3) for k in range(n - 1)})
    return target


print(sorted(cadena(4).operation_names))
