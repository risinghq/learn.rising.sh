from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator

simulador = AerSimulator(method="stabilizer", seed_simulator=3)
pm = generate_preset_pass_manager(1, simulador)

ghz100 = QuantumCircuit(100)
ghz100.h(0)
for k in range(99):
    ghz100.cx(k, k + 1)
ghz100.measure_all()

conteos_ghz = simulador.run(pm.run(ghz100), shots=1024).result().get_counts()

prediccion = 2
print(len(conteos_ghz), "cadenas distintas de", len(next(iter(conteos_ghz))), "bits")
