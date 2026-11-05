from qiskit.circuit import Measure, Parameter
from qiskit.circuit.library import CZGate, RZGate, SXGate, XGate
from qiskit.transpiler import InstructionProperties, Target


def target_durable(duracion_1q, duracion_cz):
    target = Target(num_qubits=3)
    theta = Parameter("θ")
    for puerta in (RZGate(theta), SXGate(), XGate(), Measure()):
        target.add_instruction(
            puerta, {(q,): InstructionProperties(duration=5e-8, error=1e-4) for q in range(3)}
        )
    pares = [(0, 1), (1, 2)]
    target.add_instruction(
        CZGate(), {par: InstructionProperties(duration=3e-7, error=1e-2) for par in pares}
    )
    return target
