# Wrong: always transpiles at level 1.
from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez

backend = FakeFez()

qc = QuantumCircuit(3)
qc.h(0)
qc.ccx(0, 1, 2)


def transpilar(circuito, nivel):
    pm = generate_preset_pass_manager(1, backend=backend, seed_transpiler=1)
    return pm.run(circuito)


for nivel in range(4):
    isa = transpilar(qc, nivel)
    print(f"nivel {nivel}: profundidad {isa.depth()}, {isa.count_ops().get('cz', 0)} cz")
