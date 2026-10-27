# Wrong: adds an X at the end: the circuit differs from the original.
from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez

backend = FakeFez()

qc = QuantumCircuit(3)
qc.h(0)
qc.ccx(0, 1, 2)


def transpilar(circuito, nivel):
    pm = generate_preset_pass_manager(nivel, backend=backend, seed_transpiler=1)
    isa = pm.run(circuito)
    isa.x(isa.layout.initial_index_layout()[0])
    return isa


for nivel in range(4):
    isa = transpilar(qc, nivel)
    print(f"nivel {nivel}: profundidad {isa.depth()}, {isa.count_ops().get('cz', 0)} cz")
