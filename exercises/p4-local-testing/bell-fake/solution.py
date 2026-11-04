from qiskit.circuit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_sampler import Sampler
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

fake_manila = FakeManilaV2()

bell_medido = QuantumCircuit(2)
bell_medido.h(0)
bell_medido.cx(0, 1)
bell_medido.measure_all()

isa_bell = generate_preset_pass_manager(backend=fake_manila, optimization_level=1).run(bell_medido)
sampler_fake = Sampler(mode=fake_manila, options={"simulator": {"seed_simulator": 42}})
conteos_fake = sampler_fake.run([isa_bell]).result()[0].data.meas.get_counts()

prediccion = 4096
print(sum(conteos_fake.values()), conteos_fake)
