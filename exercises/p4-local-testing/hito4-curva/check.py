import numpy as np
from scipy.linalg import expm

from qgcheck import learner, visible

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


def ising(n, J, h):
    return enlaces(n, J) + campo(n, h)


def inicial(n):
    psi = np.zeros(2**n, dtype=complex)
    psi[0] = 1
    return psi


def curva(n, U, pasos):
    psi, M, valores = inicial(n), magnetizacion(n), []
    for _ in range(pasos + 1):
        valores.append(float(np.real(np.vdot(psi, M @ psi))))
        psi = U @ psi
    return np.array(valores)


def exacta(n, J, h, dt, pasos):
    return curva(n, expm(-1j * dt * ising(n, J, h)), pasos)


def trotter(n, J, h, dt, pasos):
    return curva(n, expm(-1j * dt * campo(n, h)) @ expm(-1j * dt * enlaces(n, J)), pasos)


def leer(n, J, h, dt, pasos):
    got = learner.curvas(n, J, h, dt, pasos)
    assert isinstance(got, (list, tuple)) and len(got) == 2, f"`curvas` debe devolver dos listas, (exacta, trotter), y devuelve {got!r}."
    return np.asarray(got[0], dtype=float), np.asarray(got[1], dtype=float)


@visible("4 espines y 20 pasos: la curva exacta, la de Trotter y la distancia entre ellas")
def test_cuatro_espines():
    e, t = leer(4, 1.0, 0.5, 0.1, 20)
    assert e.shape == (21,) and t.shape == (21,), f"Con pasos = 20, las curvas de `curvas` tienen {e.size} y {t.size} puntos; deben tener 21."
    assert np.allclose(e, exacta(4, 1.0, 0.5, 0.1, 20), atol=1e-8), (
        f"La curva exacta de `curvas` es {np.round(e, 3).tolist()[:6]}…, y la evolución con exp(-iHt) da "
        f"{np.round(exacta(4, 1.0, 0.5, 0.1, 20), 3).tolist()[:6]}…"
    )
    assert np.allclose(t, trotter(4, 1.0, 0.5, 0.1, 20), atol=1e-8), f"La curva de Trotter de `curvas` es {np.round(t, 3).tolist()[:6]}…"
    assert np.max(np.abs(e - t)) < 0.05, f"Las dos curvas se separan {np.max(np.abs(e - t)):.3f}; con dt = 0.1 deben quedar a menos de 0.05."


def test_exacta_tres_espines():
    e, _ = leer(3, 0.8, 1.2, 0.2, 5)
    assert e.shape == (6,) and np.allclose(e, exacta(3, 0.8, 1.2, 0.2, 5), atol=1e-8), (
        f"Con n = 3, J = 0.8, h = 1.2, dt = 0.2 y pasos = 5, la curva exacta de `curvas` es {np.round(e, 4).tolist()}."
    )


def test_trotter_tres_espines():
    _, t = leer(3, 0.8, 1.2, 0.2, 5)
    assert t.shape == (6,) and np.allclose(t, trotter(3, 0.8, 1.2, 0.2, 5), atol=1e-8), (
        f"Con n = 3, J = 0.8, h = 1.2, dt = 0.2 y pasos = 5, la curva de Trotter de `curvas` es {np.round(t, 4).tolist()}."
    )
