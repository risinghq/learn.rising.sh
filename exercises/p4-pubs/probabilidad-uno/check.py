import numpy as np

from qgcheck import learner, visible


def close(got, angles, shots):
    """Whether P(1) follows sin²(θ/2) within five standard deviations, with the shape of the angles."""
    want = np.sin(angles / 2) ** 2
    sigma = np.sqrt(np.maximum(want * (1 - want), 0.01) / shots)
    return np.shape(got) == angles.shape and bool(np.all(np.abs(np.asarray(got) - want) < 5 * sigma))


@visible("cinco ángulos de 0 a π")
def test_five_angles():
    angles = np.linspace(0, np.pi, 5)
    got = learner.probabilidad_uno(angles, 4000)
    assert close(got, angles, 4000), f"Con cinco ángulos de 0 a π y 4000 disparos, `probabilidad_uno` devuelve {np.round(got, 3).tolist()}."


def test_any_shape():
    angles = [[0.0, 0.5, 1.0], [1.5, 2.0, 2.5]]
    got = learner.probabilidad_uno(np.array(angles), 6000)
    assert close(got, np.array(angles), 6000), f"Con angulos = {angles} y 6000 disparos, `probabilidad_uno` devuelve {np.round(got, 3).tolist()}, de forma {np.shape(got)}."


def test_a_single_angle():
    angles = np.array([np.pi / 2])
    got = learner.probabilidad_uno(angles, 8000)
    assert close(got, angles, 8000), f"Con un solo ángulo, angulos = [π/2], y 8000 disparos, `probabilidad_uno` devuelve {np.round(got, 3).tolist()}."
