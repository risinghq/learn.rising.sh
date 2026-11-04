import numpy as np

from qgcheck import learner, visible


@visible("S = ZZ − ZX + XZ + XX en cada columna")
def test_combination():
    evs = np.array([[1.0, 0.5, -1.0], [0.2, 0.1, 0.0], [0.3, -0.4, 0.5], [0.1, 0.2, -0.5]])
    got = np.asarray(learner.valor_S(evs))
    esperado = evs[0] - evs[1] + evs[2] + evs[3]
    assert got.shape == esperado.shape and np.allclose(got, esperado), f"Con 3 columnas devuelve {got.tolist()}."


def test_experiment_violates_the_classical_bound():
    S = np.asarray(learner.valor_S(learner.evs_chsh))
    assert S.shape == (13,), f"Con `evs_chsh` devuelve {S.shape[0] if S.ndim else 'un número'} valores."
    maximo = float(np.abs(S).max())
    assert maximo > 2, f"Con `evs_chsh`, |S| llega a {round(maximo, 2)}."
