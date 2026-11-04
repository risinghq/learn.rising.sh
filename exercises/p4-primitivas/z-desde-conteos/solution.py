from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorEstimator, StatevectorSampler
from qiskit.quantum_info import SparsePauliOp

ry = QuantumCircuit(3)
ry.ry(0.8, 0)

z0_estimator = float(StatevectorEstimator().run([(ry, SparsePauliOp("IIZ"))]).result()[0].data.evs)

ry_medido = ry.copy()
ry_medido.measure_all()
conteos_ry = StatevectorSampler(seed=5).run([ry_medido], shots=20000).result()[0].data.meas.get_counts()


def z_desde_conteos(conteos, k):
    total = sum(conteos.values())
    return sum(n * (1 - 2 * int(cadena[-1 - k])) for cadena, n in conteos.items()) / total


print(f"Estimator: {z0_estimator:.3f} · Sampler: {z_desde_conteos(conteos_ry, 0):.3f}")
