import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.primitives import StatevectorSampler

barrido = QuantumCircuit(1)
barrido.ry(Parameter("t"), 0)
barrido.measure_all()


def probabilidad_uno(angulos, disparos):
    pub = (barrido, np.asarray(angulos)[..., None])
    datos = StatevectorSampler(seed=2).run([pub], shots=disparos).result()[0].data
    return (1 - datos.meas.expectation_values("Z")) / 2


print(probabilidad_uno(np.linspace(0, np.pi, 5), 4000).round(3))
