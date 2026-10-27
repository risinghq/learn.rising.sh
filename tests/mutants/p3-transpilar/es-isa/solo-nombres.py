# Wrong: looks at the gate name and not at the qubits.
from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez

backend = FakeFez()

qc = QuantumCircuit(3)
qc.h(0)
qc.ccx(0, 1, 2)


def es_isa(circuito, target):
    for inst in circuito.data:
        qubits = tuple(circuito.find_bit(q).index for q in inst.qubits)
        if inst.operation.name not in target.operation_names:
            return False
    return True


isa = generate_preset_pass_manager(1, backend=backend, seed_transpiler=1).run(qc)
print("transpilado:", es_isa(isa, backend.target), "· original:", es_isa(qc, backend.target))
