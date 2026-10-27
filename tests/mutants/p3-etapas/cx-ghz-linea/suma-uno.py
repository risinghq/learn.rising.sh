# Wrong: returns one cx too many.
from qiskit import QuantumCircuit
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import CouplingMap, generate_preset_pass_manager

chip = GenericBackendV2(15, coupling_map=CouplingMap.from_line(15), seed=1)


def ghz(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    qc.cx(0, range(1, n))
    return qc


def cx_transpilado(circuito, nivel):
    pm = generate_preset_pass_manager(nivel, backend=chip, seed_transpiler=1234)
    return pm.run(circuito).count_ops().get("cx", 0) + 1


for nivel in range(4):
    print(f"nivel {nivel}: {cx_transpilado(ghz(15), nivel)} cx")
