import numpy as np
from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator

simulador = AerSimulator(method="stabilizer", seed_simulator=3)
pm = generate_preset_pass_manager(1, simulador)

angulo = np.pi / 4

con_rz = QuantumCircuit(2)
con_rz.h(0)
con_rz.rz(angulo, 0)
con_rz.cx(0, 1)
con_rz.measure_all()

try:
    conteos_rz = simulador.run(pm.run(con_rz), shots=1024).result().get_counts()
    print(conteos_rz)
except Exception as e:
    conteos_rz = None
    print("el simulador lo rechaza:", type(e).__name__)
