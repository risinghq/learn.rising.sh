from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

bell = QuantumCircuit(2)
bell.h(0)
bell.cx(1, 0)
bell.measure_all()

resultado = StatevectorSampler(seed=7).run([bell], shots=1024).result()
print(resultado[0].data.meas.get_counts())
