import math

import numpy as np

from qgcheck import learner, visible


@visible("con los puntos del GHZ el error baja de 0,001")
def test_ghz_points():
    got = learner.extrapolar_exp(learner.factores, learner.valores)
    assert abs(got - 1) < 1e-3, f"Con los `valores` del GHZ devuelve {got:.4f}."


def test_other_exponentials():
    for factores, e0, gamma in [([1, 3, 5, 7], 0.8, 0.07), ([1, 2], 1.0, -np.log(0.9))]:
        valores = [round(float(e0 * np.exp(-gamma * c)), 4) for c in factores]
        got = learner.extrapolar_exp(factores, valores)
        assert math.isclose(got, e0, abs_tol=1e-3), (
            f"Con factores = {factores} y valores = {valores} devuelve {round(got, 4)}."
        )
