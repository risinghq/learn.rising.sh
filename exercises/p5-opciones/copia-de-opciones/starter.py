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
isa_bell = pm.run(bell)
zz = SparsePauliOp("ZZ").apply_layout(isa_bell.layout)


def medir_zz(estimator):
    """Devuelve el error estándar de ⟨ZZ⟩ del Bell con el Estimator que recibe."""
    estimator.options.simulator.seed_simulator = 7
    return float(estimator.run([(isa_bell, zz)]).result()[0].data.stds)


# `est` debe usar 5000 disparos.
opts = {"default_shots": 100}
est = Estimator(mode=backend, options=opts)
opts["default_shots"] = 5000

error = medir_zz(est)
print("default_shots =", est.options.default_shots, "· error de ⟨ZZ⟩ =", round(error, 4))
