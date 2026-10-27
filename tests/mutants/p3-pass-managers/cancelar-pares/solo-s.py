# Wrong: cancels only S and S†.
from qiskit import QuantumCircuit
from qiskit.circuit.library import HGate, SdgGate, SGate
from qiskit.transpiler import PassManager, generate_preset_pass_manager
from qiskit.transpiler.passes import InverseCancellation
from qiskit_ibm_runtime.fake_provider import FakeFez

con_pares = QuantumCircuit(2)
con_pares.h(0)
con_pares.s(0)
con_pares.sdg(0)
con_pares.cx(0, 1)
con_pares.h(1)
con_pares.h(1)
con_pares.x(1)

sin_pares = QuantumCircuit(2)
sin_pares.h(0)
sin_pares.cx(0, 1)
sin_pares.x(1)

fez = FakeFez()
pm_nivel0 = generate_preset_pass_manager(0, backend=fez, seed_transpiler=1)
pm_nivel0.pre_layout = PassManager([InverseCancellation([(SGate(), SdgGate())])])

puertas_con = dict(pm_nivel0.run(con_pares).count_ops())
puertas_ref = dict(generate_preset_pass_manager(0, backend=fez, seed_transpiler=1).run(sin_pares).count_ops())
print("con pares:", puertas_con, "· sin pares:", puertas_ref)
