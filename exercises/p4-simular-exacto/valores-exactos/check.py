import numpy as np

from qgcheck import learner, visible


@visible("tu apuesta son los tres valores exactos")
def test_bet():
    bet = learner.prediccion
    assert isinstance(bet, (list, tuple)) and len(bet) == 3, (
        "Escribe en `prediccion` una lista con tres números, uno por cada valor de `theta`.")
    assert np.allclose(bet, learner.exacto, atol=0.05), (
        "Tu apuesta no coincide con lo que calcula Estimator. Calcula cada valor con el estado que deja el circuito para ese `theta`.")


def test_same_program():
    got = np.round(learner.exacto, 3).tolist()
    assert np.allclose(got, [4, 2 + np.sqrt(3), 2], atol=1e-3), (
        f"`exacto` vale ahora {got}; el circuito, el observable o los valores de la lección cambiaron.")
