from qiskit import QuantumCircuit
from qiskit.primitives import BackendSamplerV2, StatevectorSampler
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import generate_preset_pass_manager

bell_medido = QuantumCircuit(2)
bell_medido.h(0)
bell_medido.cx(0, 1)
bell_medido.measure_all()

backend = GenericBackendV2(2, seed=1)
isa_bell = generate_preset_pass_manager(1, backend=backend).run(bell_medido)

sampler = BackendSamplerV2(backend=backend, options={"seed_simulator": 3})

conteos_backend = sampler.run([isa_bell], shots=1024).result()[0].data.meas.get_counts()
print(type(sampler).__name__, conteos_backend)
