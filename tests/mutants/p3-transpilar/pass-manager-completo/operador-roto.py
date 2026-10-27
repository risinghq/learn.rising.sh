# Wrong: the pass manager is ISA but adds an X at the end.
from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez

backend = FakeFez()

qc = QuantumCircuit(3)
qc.h(0)
qc.ccx(0, 1, 2)


def pass_manager(nivel):
    pm = generate_preset_pass_manager(optimization_level=nivel, backend=backend, seed_transpiler=1)
    def run(c):
        isa = pm.run(c)
        isa.x(isa.layout.initial_index_layout()[0])
        return isa
    return type('P', (), {'run': staticmethod(run)})()


print(sorted(pass_manager(1).run(qc).count_ops()))
