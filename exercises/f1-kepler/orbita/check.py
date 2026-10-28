import math

from qgcheck import learner, visible


def energia(estado):
    x, y, vx, vy = estado
    return 0.5 * (vx * vx + vy * vy) - 1 / math.hypot(x, y)


def momento(estado):
    x, y, vx, vy = estado
    return x * vy - y * vx


ELIPSE = (1.25, 0.0, 0.0, 0.8)


@visible("órbita circular: tras un cuarto de periodo el planeta está en (0, 1)")
def test_quarter_period():
    got = learner.orbita(1.0, 0.0, 0.0, 1.0, 2 * math.pi / 1000, 250)
    assert math.dist(got[:2], (0.0, 1.0)) < 1e-3, (
        f"Con x = 1.0, y = 0.0, vx = 0.0, vy = 1.0, dt = 2π/1000 y pasos = 250, `orbita` devuelve {got!r}.")


@visible("órbita circular: tras un periodo vuelve al punto de partida")
def test_full_period():
    got = learner.orbita(1.0, 0.0, 0.0, 1.0, 2 * math.pi / 1000, 1000)
    assert math.dist(got[:2], (1.0, 0.0)) < 1e-3, (
        f"Con x = 1.0, y = 0.0, vx = 0.0, vy = 1.0, dt = 2π/1000 y pasos = 1000, `orbita` devuelve {got!r}.")


def test_energy_at_closest_approach():
    got = learner.orbita(*ELIPSE, 0.02, 167)
    assert abs(energia(got) - energia(ELIPSE)) < 1.5e-4, (
        f"Con x = 1.25, y = 0.0, vx = 0.0, vy = 0.8, dt = 0.02 y pasos = 167, `orbita` devuelve {got!r}.")


def test_energy_and_momentum_after_three_orbits():
    got = learner.orbita(*ELIPSE, 0.02, 1000)
    assert abs(energia(got) - energia(ELIPSE)) < 1e-4 and abs(momento(got) - momento(ELIPSE)) < 1e-9, (
        f"Con x = 1.25, y = 0.0, vx = 0.0, vy = 0.8, dt = 0.02 y pasos = 1000, `orbita` devuelve {got!r}.")
