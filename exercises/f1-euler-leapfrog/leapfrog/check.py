import numpy as np

from qgcheck import learner, visible


def close(got, want, tol=1e-9):
    return np.allclose(got, want, rtol=0, atol=tol)


@visible("un paso desde x = 1, v = 0 con dt = 0.1")
def test_one_step():
    got = learner.leapfrog(1.0, 0.0, 0.1, 1)
    assert close(got, (0.995, -0.09975)), (
        f"Con x = 1.0, v = 0.0, dt = 0.1 y pasos = 1, `leapfrog` devuelve {got!r}.")


@visible("cero pasos deja el estado como estaba")
def test_no_steps():
    got = learner.leapfrog(0.3, -0.7, 0.1, 0)
    assert close(got, (0.3, -0.7)), (
        f"Con x = 0.3, v = -0.7, dt = 0.1 y pasos = 0, `leapfrog` devuelve {got!r}.")


def test_ten_steps():
    got = learner.leapfrog(1.0, 0.0, 0.1, 10)
    assert close(got, (0.5399512509335086, -0.8406435124348495)), (
        f"Con x = 1.0, v = 0.0, dt = 0.1 y pasos = 10, `leapfrog` devuelve {got!r}.")


def test_starts_with_speed():
    got = learner.leapfrog(0.0, 1.0, 0.05, 40)
    assert close(got, (0.9094949470256556, -0.416336317772622)), (
        f"Con x = 0.0, v = 1.0, dt = 0.05 y pasos = 40, `leapfrog` devuelve {got!r}.")


def test_energy_after_many_steps():
    got = learner.leapfrog(1.0, 0.0, 0.1, 10000)
    energia = 0.5 * (got[0] ** 2 + got[1] ** 2)
    assert abs(energia - 0.5) < 0.005, (
        f"Con x = 1.0, v = 0.0, dt = 0.1 y pasos = 10000, `leapfrog` devuelve {got!r}.")
