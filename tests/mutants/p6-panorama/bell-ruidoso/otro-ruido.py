from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error


def modelo_ruido(p_cx, p_lectura):
    """Ruido despolarizante en cada CX y una lectura que se equivoca con probabilidad p_lectura."""
    modelo = NoiseModel()
    modelo.add_all_qubit_quantum_error(depolarizing_error(p_cx, 2), ["cx"])
    modelo.add_all_qubit_readout_error(
        ReadoutError([[1 - p_lectura, p_lectura], [p_lectura, 1 - p_lectura]])
    )
    return modelo


def medir(qc, modelo, shots=4000):
    sim = AerSimulator(noise_model=modelo, seed_simulator=7)
    return sim.run(qc, shots=shots).result().get_counts()


def fraccion_erronea(cuentas):
    """Fracción de disparos que ningún Bell ideal produciría: 01 o 10."""
    return (cuentas.get("01", 0) + cuentas.get("10", 0)) / sum(cuentas.values())


bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)
bell.measure_all()

cuentas_bell = medir(bell, modelo_ruido(0.2, 0.02), shots=1000)
print(dict(sorted(cuentas_bell.items())))

# ✏️ cuenta los disparos que dieron 01 o 10
erroneos = cuentas_bell.get("01", 0) + cuentas_bell.get("10", 0)
print(f"disparos erróneos: {erroneos} de {sum(cuentas_bell.values())}")

# ✏️ apuesta antes de mirar la línea de arriba: ¿10, 160 o 1500 disparos erróneos?
prediccion = 160
