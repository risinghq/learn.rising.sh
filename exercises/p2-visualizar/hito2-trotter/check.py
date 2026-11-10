import numpy as np
from scipy.linalg import expm

from qgcheck import learner, operator, visible

X = np.array([[0, 1], [1, 0]], dtype=complex)
Z = np.diag([1.0, -1.0]).astype(complex)


def sobre(n, ops):
    """El producto de Kronecker con ops[q] en el qubit q; Qiskit pone el qubit 0 a la derecha."""
    m = np.eye(1, dtype=complex)
    for q in reversed(range(n)):
        m = np.kron(m, ops.get(q, np.eye(2)))
    return m


def enlaces(n, J):
    return sum((J * sobre(n, {i: Z, i + 1: Z}) for i in range(n - 1)), np.zeros((2**n, 2**n)))


def campo(n, h):
    return sum(h * sobre(n, {i: X}) for i in range(n))


def magnetizacion(n):
    return sum(sobre(n, {i: Z}) for i in range(n)) / n


def trotter_exacto(n, J, h, dt, pasos):
    paso = expm(-1j * dt * campo(n, h)) @ expm(-1j * dt * enlaces(n, J))
    return np.linalg.matrix_power(paso, pasos)


def matriz(n, J, h, dt, pasos):
    return np.asarray(operator(learner.trotter(n, J, h, dt, pasos)).data)


def igual_salvo_fase(a, b):
    return a.shape == b.shape and np.isclose(abs(np.vdot(a, b)) / len(a), 1, atol=1e-8)


def m_final(n, u):
    psi = u[:, 0]
    return round(float(np.real(np.vdot(psi, magnetizacion(n) @ psi))), 4)


@visible("cinco pasos de 3 espines dan el operador (e^{-i dt hΣX} e^{-i dt JΣZZ})⁵")
def test_cinco_pasos():
    got = matriz(3, 1.0, 0.5, 0.1, 5)
    assert got.shape == (8, 8), f"`trotter` devuelve un circuito de {int(np.log2(len(got)))} qubits y deben ser 3."
    assert igual_salvo_fase(got, trotter_exacto(3, 1.0, 0.5, 0.1, 5)), (
        f"Con n = 3, J = 1.0, h = 0.5, dt = 0.1 y pasos = 5, `trotter` deja M_Z = {m_final(3, got)} "
        f"desde |000⟩, y cinco pasos de Trotter dejan {m_final(3, trotter_exacto(3, 1.0, 0.5, 0.1, 5))}."
    )


def test_cuatro_espines():
    got = matriz(4, 0.8, 1.1, 0.2, 3)
    assert igual_salvo_fase(got, trotter_exacto(4, 0.8, 1.1, 0.2, 3)), (
        f"Con n = 4, J = 0.8, h = 1.1, dt = 0.2 y pasos = 3, `trotter` deja M_Z = {m_final(4, got)} desde |0000⟩."
    )
