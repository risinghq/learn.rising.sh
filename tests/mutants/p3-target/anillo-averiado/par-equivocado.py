# Wrong: removes the pair (3, 0) instead of the faulty one.
from qiskit import QuantumCircuit
from qiskit.circuit import Measure, Parameter
from qiskit.circuit.library import CZGate, RZGate, SXGate, XGate
from qiskit.transpiler import InstructionProperties, Target, generate_preset_pass_manager

errores_cz = {
    (0, 1): 5e-3,
    (2, 3): 5e-3,
    (1, 2): 5e-3,
}

anillo = Target("anillo de 4", num_qubits=4)
anillo.add_instruction(RZGate(Parameter("t")), {(q,): InstructionProperties(error=0.0, duration=0.0) for q in range(4)})
for puerta in (XGate(), SXGate(), Measure()):
    anillo.add_instruction(puerta, {(q,): None for q in range(4)})
anillo.add_instruction(CZGate(), {par: InstructionProperties(error=e) for par, e in errores_cz.items()})

bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)
isa = generate_preset_pass_manager(3, target=anillo, seed_transpiler=1).run(bell)
print("pares de dos qubits usados:", [tuple(isa.find_bit(q).index for q in i.qubits) for i in isa.data if i.operation.num_qubits == 2])
