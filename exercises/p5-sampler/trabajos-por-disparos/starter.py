from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_sampler import Sampler
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

backend = FakeManilaV2()
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)

bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)
bell.measure_all()
isa = pm.run(bell)

sampler = Sampler(mode=backend)
sampler.options.default_shots = 4000
sampler.options.simulator.seed_simulator = 11

try:
    resultado = sampler.run([(isa, None, 64), (isa, None, 128)]).result()
    disparos = [pub.data.meas.num_shots for pub in resultado]
except Exception as error:
    disparos = []
    print("Error:", error)
print(disparos)
