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


def medir_zz(disparos):
    """Devuelve ⟨ZZ⟩ del Bell y su error estándar con ese número de disparos."""
    estimator = Estimator(mode=backend)
    estimator.options.default_shots = disparos
    estimator.options.simulator.seed_simulator = 7
    datos = estimator.run([(isa, zz)]).result()[0].data
    return float(datos.evs), float(datos.stds)


disparos = 20000
valor, error = medir_zz(disparos)
print(f"{disparos} disparos → ⟨ZZ⟩ = {valor:.3f} ± {error:.4f}")
