import math

from qgcheck import learner, visible


@visible("el cuadrado de la precisión")
def test_inverse_square():
    eps = 0.01
    va = 20
    got = learner.tiempo_qpu(eps, va)
    mitad = learner.tiempo_qpu(eps / 2, va)
    assert abs((mitad - 60) / (got - 60) - 4) < 1e-9, (
        f"Con eps = {eps} y va = {va}, `tiempo_qpu` devuelve {got}."
    )


def test_volume():
    eps, va = 0.02, 10
    base = learner.tiempo_qpu(eps, va) - 60
    doble = learner.tiempo_qpu(eps, va + 1) - 60
    assert abs(doble / base - math.exp(0.35)) < 1e-9, (
        f"Con eps = {eps} y va = {va}, `tiempo_qpu` devuelve {base + 60}."
    )
