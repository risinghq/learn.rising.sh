# Wrong: adds a pair between the first and the last qubit.
from qiskit.circuit import Measure, Parameter
from qiskit.circuit.library import CZGate, RZGate, SXGate, XGate
from qiskit.transpiler import InstructionProperties, Target


def cadena(n):
    target = Target(f"cadena de {n}", num_qubits=n)
    target.add_instruction(RZGate(Parameter("t")), {(q,): None for q in range(n)})
    for puerta in (XGate(), SXGate(), Measure()):
        target.add_instruction(puerta, {(q,): None for q in range(n)})
    target.add_instruction(CZGate(), {(k, k + 1): InstructionProperties(error=5e-3) for k in range(n - 1)} | {(0, n - 1): InstructionProperties(error=5e-3)})
    return target


print(sorted(cadena(4).operation_names))
