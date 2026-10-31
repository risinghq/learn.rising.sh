import numpy as np

from qgcheck import learner, visible


def close(got, want, tol=1e-9):
    return np.allclose(got, want, rtol=0, atol=tol)


def energia(estado):
    return 0.5 * (estado[0] ** 2 + estado[1] ** 2)


@visible("un paso desde x = 1, v = 1 con dt = 0.1")
def test_one_step():
    got = learner.euler(1.0, 1.0, 0.1, 1)
    assert close(got, (1.1, 0.9)), (
        f"Con x = 1.0, v = 1.0, dt = 0.1 y pasos = 1, `euler` devuelve {got!r}.")


@visible("la energía crece en cada paso: tras 100 pasos pasa de 0.5 a 1.3524")
def test_energy_grows():
    got = learner.euler(1.0, 0.0, 0.1, 100)
    assert abs(energia(got) - 1.3524069) < 1e-5, (
        f"Con x = 1.0, v = 0.0, dt = 0.1 y pasos = 100, `euler` devuelve {got!r}.")


def test_ten_steps():
    got = learner.euler(1.0, 0.0, 0.1, 10)
    assert close(got, (0.5707904498999999, -0.8825080100000001)), (
        f"Con x = 1.0, v = 0.0, dt = 0.1 y pasos = 10, `euler` devuelve {got!r}.")


def test_energy_with_a_small_step():
    got = learner.euler(1.0, 0.0, 0.01, 1000)
    assert abs(energia(got) - 0.5525827) < 1e-5, (
        f"Con x = 1.0, v = 0.0, dt = 0.01 y pasos = 1000, `euler` devuelve {got!r}.")
