import numpy as np
from qiskit.circuit.library import efficient_su2
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator

simulador = AerSimulator(method="stabilizer", seed_simulator=3)
pm = generate_preset_pass_manager(1, simulador)


def a_clifford(params):
    # ✏️ redondea cada ángulo al múltiplo de π/2 más cercano
    return np.asarray(params)


base = efficient_su2(12)
params = np.random.default_rng(7).uniform(0, 2 * np.pi, base.num_parameters)

medido = base.copy()
medido.measure_all()
try:
    conteos = simulador.run(pm.run(medido.assign_parameters(a_clifford(params))), shots=1024).result().get_counts()
    print(len(conteos), "cadenas distintas de 12 bits")
except Exception as e:
    print("el simulador lo rechaza:", type(e).__name__)
