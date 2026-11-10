import numpy as np
from scipy.linalg import expm

from qgcheck import learner, operator, visible

X = np.array([[0, 1], [1, 0]], dtype=complex)
Z = np.diag([1.0, -1.0]).astype(complex)
I2 = np.eye(2, dtype=complex)


def paso_exacto(J, h, dt):
    """exp(-i dt h (XI + IX)) · exp(-i dt J ZZ): el paso de Trotter de dos espines."""
    zz = J * np.kron(Z, Z)
    x = h * (np.kron(X, I2) + np.kron(I2, X))
    return expm(-1j * dt * x) @ expm(-1j * dt * zz)


def matriz(J, h, dt):
    return np.asarray(operator(learner.paso(J, h, dt)).data)


def igual_salvo_fase(a, b):
    return a.shape == b.shape and np.isclose(abs(np.vdot(a, b)) / len(a), 1, atol=1e-8)


def probabilidades(u):
    return np.round(np.abs(u[:, 0]) ** 2, 4).tolist()


@visible("el circuito aplica exp(-i dt h X) · exp(-i dt J ZZ) a los dos espines")
def test_paso():
    got = matriz(1.0, 0.5, 0.1)
    assert got.shape == (4, 4), f"`paso` devuelve un circuito de {int(np.log2(len(got)))} qubits y deben ser 2."
    assert igual_salvo_fase(got, paso_exacto(1.0, 0.5, 0.1)), (
        f"Con J = 1.0, h = 0.5 y dt = 0.1, tu paso lleva |00⟩ a las probabilidades {probabilidades(got)}, "
        f"y el paso de Trotter da {probabilidades(paso_exacto(1.0, 0.5, 0.1))}."
    )


def test_otros_parametros():
    got = matriz(0.7, 1.2, 0.25)
    assert igual_salvo_fase(got, paso_exacto(0.7, 1.2, 0.25)), (
        f"Con J = 0.7, h = 1.2 y dt = 0.25, `paso` lleva |00⟩ a las probabilidades {probabilidades(got)}."
    )
