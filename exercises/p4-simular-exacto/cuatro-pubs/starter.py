import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

qubit = QuantumCircuit(1)
qubit.ry(1.0, 0)
qubit.measure_all()
p1_exacto = np.sin(0.5) ** 2


def errores_por_disparos(sampler, disparos):
    pubs = []   # ✏️ un PUB (qubit, None, n) por cada cantidad de disparos n
    errores = []   # ✏️ |P(1) estimada − p1_exacto| de cada PUB, con get_counts()
    return errores


errores = errores_por_disparos(StatevectorSampler(seed=11), [100, 1000, 10_000, 100_000])
print([round(float(e), 4) for e in errores])
