from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError


def modelo_lectura(p01, p10):
    ruido = NoiseModel()
    # ✏️ añade el ReadoutError con ruido.add_all_qubit_readout_error(...)
    return ruido


uno = QuantumCircuit(1)
uno.x(0)
uno.measure_all()

sim = AerSimulator(noise_model=modelo_lectura(0.05, 0.10), seed_simulator=5)
c_uno = sim.run(generate_preset_pass_manager(1, backend=sim).run(uno), shots=20000).result().get_counts()
print(c_uno, f"· lee 0 el {c_uno.get('0', 0) / 20000:.1%} de las veces")
