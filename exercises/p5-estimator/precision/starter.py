from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

backend = FakeManilaV2()
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)

bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)
isa = pm.run(bell)
zz = SparsePauliOp("ZZ").apply_layout(isa.layout)

estimator = Estimator(mode=backend)
estimator.options.simulator.seed_simulator = 7
estimator.options.default_precision = 0.05

datos = estimator.run([(isa, zz)], precision=0.05).result()[0].data
error_zz = float(datos.stds)
print(f"⟨ZZ⟩ = {float(datos.evs):.3f} ± {error_zz:.4f}")
