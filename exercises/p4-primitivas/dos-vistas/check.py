import numpy as np

from qgcheck import learner, visible


@visible("tu apuesta son los tres valores esperados")
def test_bet():
    bet = learner.prediccion
    assert isinstance(bet, (list, tuple)) and len(bet) == 3, (
        "Escribe en `prediccion` una lista con tres números: ⟨ZZ⟩, ⟨ZI⟩ y ⟨XX⟩.")
    assert np.allclose(bet, learner.evs, atol=0.05), (
        "Tu apuesta no coincide con lo que calcula Estimator. Piensa qué da cada observable en un estado en el que los dos qubits siempre coinciden.")


def test_same_state():
    got = np.round(learner.evs, 3).tolist()
    assert np.allclose(got, [1, 0, 1]), (
        f"`evs` vale ahora {got}; el circuito o los observables de la lección cambiaron.")
