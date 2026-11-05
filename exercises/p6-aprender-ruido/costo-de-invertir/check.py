import math

from qgcheck import inside, learner, visible


@inside
def rates():
    return [float(r) for r in learner.modelo.rates]


@visible("`gamma_capa` es el coste de invertir el modelo")
def test_gamma():
    esperado = math.exp(2 * sum(rates()))
    assert abs(learner.gamma_capa - esperado) < 1e-9, f"`gamma_capa` vale {learner.gamma_capa:.5f}."


@visible("tu apuesta coincide con `gamma_capa`")
def test_bet():
    real = "mayor que 1" if learner.gamma_capa > 1 else "menor que 1"
    assert learner.prediccion == real, (
        f"Apostaste {learner.prediccion!r}, pero `gamma_capa` vale {learner.gamma_capa:.5f}."
    )


def test_model_is_the_lesson_model():
    tasas = rates()
    assert sorted(tasas) == [0.002, 0.005, 0.01], f"Las tasas de `modelo` son {tasas}."
