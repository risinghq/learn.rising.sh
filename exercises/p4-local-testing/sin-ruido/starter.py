from qiskit.circuit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.executor_sampler import Sampler
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

fake_manila = FakeManilaV2()

bell_medido = QuantumCircuit(2)
bell_medido.h(0)
bell_medido.cx(0, 1)
bell_medido.measure_all()

backend = fake_manila   # ✏️ cambia a AerSimulator()

isa_local = generate_preset_pass_manager(backend=backend, optimization_level=1).run(bell_medido)
sampler_local = Sampler(mode=backend, options={"simulator": {"seed_simulator": 42}})
conteos_local = sampler_local.run([isa_local]).result()[0].data.meas.get_counts()
print(type(backend).__name__, conteos_local)
