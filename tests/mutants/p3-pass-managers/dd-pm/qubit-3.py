# Wrong: fills only qubit 3.
from qiskit import QuantumCircuit
from qiskit.circuit.library import XGate
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import PassManager, generate_preset_pass_manager
from qiskit.transpiler.passes.scheduling import ALAPScheduleAnalysis, PadDynamicalDecoupling

backend5 = GenericBackendV2(5, seed=1)
objetivo = backend5.target

ghz5 = QuantumCircuit(5)
ghz5.h(0)
ghz5.cx(0, range(1, 5))
programado = generate_preset_pass_manager(
    1, backend=backend5, scheduling_method="asap", seed_transpiler=1234
).run(ghz5)

dd_pm = PassManager([
    ALAPScheduleAnalysis(target=objetivo),
    PadDynamicalDecoupling(qubits=[3], target=objetivo, dd_sequence=[XGate(), XGate()]),
])
con_dd = dd_pm.run(programado)
print("x antes:", programado.count_ops().get("x", 0), "· x después:", con_dd.count_ops().get("x", 0))
