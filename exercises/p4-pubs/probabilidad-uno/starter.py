import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.primitives import StatevectorSampler

barrido = QuantumCircuit(1)
barrido.ry(Parameter("t"), 0)
barrido.measure_all()


def probabilidad_uno(angulos, disparos):
    # ✏️ un solo PUB de StatevectorSampler y expectation_values("Z") sobre datos.meas
    return np.zeros(np.shape(angulos))


print(probabilidad_uno(np.linspace(0, np.pi, 5), 4000).round(3))
