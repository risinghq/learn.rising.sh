import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp

from qgcheck import learner, visible


def max_error(precision):
    circuito = QuantumCircuit(2)
    circuito.ry(Parameter("theta"), 0)
    circuito.h(0)
    circuito.cx(0, 1)
    observable = SparsePauliOp(["II", "XX", "YY", "ZZ"], coeffs=[1, 1, -1, 1])
    valores = [[0], [np.pi / 6], [np.pi / 2]]
    exacto = StatevectorEstimator().run([(circuito, observable, valores)]).result()[0].data.evs
    ruidoso = StatevectorEstimator(seed=1).run([(circuito, observable, valores)], precision=precision).result()[0].data.evs
    return float(np.abs(ruidoso - exacto).max())


@visible("el error máximo queda por debajo de 0.02")
def test_small_error():
    error = learner.error_max
    assert error < 0.02, f"El error máximo es {error:.4f}. Baja `precision`: pide menos error estadístico."


def test_still_noisy():
    error = learner.error_max
    assert error > 0, f"Con precision = {learner.precision}, `error_max` vale {error}: ya no hay ruido de muestreo."


def test_error_comes_from_the_estimator():
    precision = learner.precision
    error = max_error(precision)
    assert 0 < error < 0.02, f"Con precision = {precision}, el error máximo del Estimator es {error:.4f}."
