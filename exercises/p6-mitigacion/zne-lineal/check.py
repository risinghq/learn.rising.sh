import numpy as np

from qgcheck import learner, visible


@visible("`zne_lineal` es el valor en el factor 0 de la recta")
def test_linear_fit():
    esperado = float(np.polyfit(learner.factores, learner.valores, 1)[1])
    assert abs(learner.zne_lineal - esperado) < 1e-9, (
        f"`zne_lineal` vale {learner.zne_lineal:.4f}, con valores = {np.round(learner.valores, 4).tolist()}."
    )


@visible("tu apuesta coincide con lo que da la recta")
def test_bet():
    z = learner.zne_lineal
    real = "llega a 1" if abs(z - 1) < 1e-3 else ("se pasa" if z > 1 else "se queda corta")
    assert learner.prediccion == real, (
        f"Apostaste {learner.prediccion!r}, pero `zne_lineal` vale {z:.4f}."
    )


def test_measurements_are_the_ghz_ones():
    assert learner.factores == [1, 3, 5], f"`factores` vale {learner.factores}."
    valores = [round(v, 2) for v in learner.valores]
    assert valores == [0.94, 0.83, 0.74], f"Con `factores` = [1, 3, 5], `valores` es {valores}."
