from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

fake_manila = FakeManilaV2()

bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)

isa_estado = generate_preset_pass_manager(backend=fake_manila, optimization_level=1).run(bell)
zz = SparsePauliOp("ZZ").apply_layout(isa_estado.layout)


def ev_zz(mitigar):
    estimator = Estimator(mode=fake_manila, options={"simulator": {"seed_simulator": 1}})
    # ✏️ activa o desactiva estimator.options.resilience.measure_mitigation según `mitigar`
    return float(estimator.run([(isa_estado, zz)]).result()[0].data.evs)


sin_mitigar, mitigado = ev_zz(False), ev_zz(True)
print(f"sin mitigar {sin_mitigar:.3f} · mitigado {mitigado:.3f}")
