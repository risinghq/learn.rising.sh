import numpy as np

from qgcheck import learner, visible


@visible("dos espines y tres términos")
def test_default():
    got = learner.hamiltoniano(1.0, 0.5)
    esperado = np.array([[1.0, 0.5, 0.5, 0], [0.5, -1.0, 0, 0.5], [0.5, 0, -1.0, 0.5], [0, 0.5, 0.5, 1.0]])
    assert got.num_qubits == 2 and np.allclose(got.to_matrix(), esperado), f"Con J = 1.0 y h = 0.5, `hamiltoniano` devuelve {got}."


def test_other_parameters():
    got = learner.hamiltoniano(-0.3, 1.2)
    assert np.allclose(got.to_matrix(), np.array([[-0.3, 1.2, 1.2, 0], [1.2, 0.3, 0, 1.2], [1.2, 0, 0.3, 1.2], [0, 1.2, 1.2, -0.3]])), f"Con J = -0.3 y h = 1.2, `hamiltoniano` devuelve {got.to_matrix().tolist()}."
