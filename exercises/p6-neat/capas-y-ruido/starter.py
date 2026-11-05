import random

import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.debug_tools import Neat
from qiskit_ibm_runtime.fake_provider import FakeManilaV2


def circuito_espejo(n_qubits, capas):
    """Rotaciones RZ aleatorias y CX, seguidas de su inverso: cada ⟨Z⟩ ideal vale 1."""
    rng = random.Random(10)
    angulos = [[rng.random() for _ in range(n_qubits)] for _ in range(capas)]
    qc = QuantumCircuit(n_qubits)
    qubits = list(range(n_qubits))

    def pares(capa):
        return qubits[::2] if capa % 2 == 0 else qubits[1 : n_qubits - 1 : 2]

    for capa in range(capas):
        for q in qubits:
            qc.rz(angulos[capa][q], q)
        for q in pares(capa):
            qc.cx(q, q + 1)
    for capa in reversed(range(capas)):
        for q in pares(capa):
            qc.cx(q, q + 1)
        for q in qubits:
            qc.rz(-angulos[capa][q], q)
    return qc


def diferencia_media(ideal, ruidoso):
    """Diferencia absoluta media entre dos NeatResult, en porcentaje, por PUB."""
    return [float(np.mean(abs(i - r).vals) * 100) for i, r in zip(ideal, ruidoso)]


fake = FakeManilaV2()
pm = generate_preset_pass_manager(backend=fake, optimization_level=0)


def pubs_con_capas(capas):
    """Un PUB por número de capas, con los cuatro ⟨Z_i⟩ ya mapeados al layout."""
    pubs = []
    for n in capas:
        isa = pm.run(circuito_espejo(4, n))
        observables = [
            SparsePauliOp("I" * (3 - i) + "Z" + "I" * i).apply_layout(isa.layout) for i in range(4)
        ]
        pubs.append((isa, observables))
    return pubs


analizador = Neat(fake)
pubs_cliff = analizador.to_clifford(pubs_con_capas([1, 2, 3]))
ideal = analizador.ideal_sim(pubs_cliff, seed_simulator=1)

# ✏️ simula los mismos PUBs con el modelo de ruido del backend (seed_simulator=1)
ruidoso = ideal
dif_backend = diferencia_media(ideal, ruidoso)
for capas, d in zip([1, 2, 3], dif_backend):
    print(f"{capas} capas: {d:.2f} %")

# ✏️ apuesta antes de mirar las líneas de arriba: la diferencia a 3 capas, ¿"menor", "parecida" o "mayor" que a 1 capa?
prediccion = ""
