import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

qubit = QuantumCircuit(1)
qubit.ry(1.0, 0)
qubit.measure_all()
p1_exacto = np.sin(0.5) ** 2


def errores_por_disparos(sampler, disparos):
    pubs = [(qubit, None, n) for n in disparos]
    resultado = sampler.run(pubs).result()
    return [abs(r.data.meas.get_counts().get("1", 0) / r.data.meas.num_shots - p1_exacto) for r in resultado]


errores = errores_por_disparos(StatevectorSampler(seed=11), [100, 1000, 10_000, 100_000])
print([round(float(e), 4) for e in errores])
