from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_sampler import Sampler
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

backend = FakeManilaV2()
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)

ghz = QuantumCircuit(5)
ghz.h(0)
for i in range(4):
    ghz.cx(i, i + 1)
ghz.measure_all()
isa = pm.run(ghz)

sampler = Sampler(mode=backend)
sampler.options.default_shots = 4000
sampler.options.simulator.seed_simulator = 11
conteos = sampler.run([isa]).result()[0].data.meas.get_counts()

# ✏️ cuenta los disparos que dieron 00000 o 11111
ideales = 0
fraccion_ruido = 1 - ideales / sum(conteos.values())
print(f"{fraccion_ruido:.1%} de los disparos tiene algún bit cambiado")

# ✏️ apuesta antes de mirar la línea de arriba: ¿1 %, 20 % o 60 %?
prediccion = 0.0
