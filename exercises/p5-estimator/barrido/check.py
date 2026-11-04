import numpy as np

from qgcheck import learner, visible


@visible("`evs` tiene 3 observables × 100 juegos de parámetros")
def test_shape():
    forma = tuple(learner.evs.shape)
    assert forma == (3, 100), f"`evs` tiene forma {forma}."


@visible("tu apuesta coincide con la forma de `evs`")
def test_bet():
    forma = tuple(learner.evs.shape)
    apuesta = tuple(learner.prediccion)
    assert apuesta == forma, f"Apostaste {apuesta}, pero `evs` tiene forma {forma}."


def test_first_observable_is_the_mixture():
    evs = learner.evs
    assert evs.shape == (3, 100), f"`evs` tiene forma {evs.shape}."
    peor = float(np.max(np.abs(evs[0] - 0.5 * evs[1] - 0.5 * evs[2])))
    assert peor < 0.4, f"En `evs`, el primer observable se aleja hasta {peor:.2f} de la mezcla de los otros dos."
