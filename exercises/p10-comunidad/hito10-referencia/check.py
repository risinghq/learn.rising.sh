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


def leer(n, J, h, T, pasos):
    got = learner.curvas(n, J, h, T, pasos)
    assert isinstance(got, (list, tuple)) and len(got) == 2, f"`curvas` debe devolver (exacta, trotter) y devuelve {got!r}."
    return np.asarray(got[0], dtype=float), np.asarray(got[1], dtype=float)


@visible("4 espines, T = 2 y 20 pasos: M(0) = 1, las dos curvas y menos de 0.01 entre ellas")
def test_veinte_pasos():
    e, t = leer(4, 1.0, 1.0, 2.0, 20)
    assert e.shape == (21,) and t.shape == (21,), f"Con pasos = 20, tus curvas tienen {e.size} y {t.size} puntos; cada una lleva t = 0 y t = T."
    assert np.allclose(e, exacta(4, 1.0, 1.0, 0.1, 20), atol=1e-6), (
        f"Tu curva exacta empieza {np.round(e[:4], 4).tolist()}…; en cada t = k · T / pasos evoluciona |0000⟩ con e^(-iHt)."
    )
    assert np.allclose(t, trotter(4, 1.0, 1.0, 0.1, 20), atol=1e-6), (
        f"Tu curva de Trotter empieza {np.round(t[:4], 4).tolist()}…; cada paso usa dt = T / pasos."
    )
    peor = float(np.max(np.abs(e - t)))
    assert peor < 0.01, f"Con 20 pasos tus curvas se separan hasta {peor:.4f}."


def test_tres_espines():
    e, t = leer(3, 0.7, 1.3, 1.5, 6)
    assert e.shape == t.shape == (7,), f"Con n = 3, T = 1.5 y pasos = 6, `curvas` devuelve {e.size} y {t.size} puntos."
    assert np.allclose(e, exacta(3, 0.7, 1.3, 0.25, 6), atol=1e-6) and np.allclose(t, trotter(3, 0.7, 1.3, 0.25, 6), atol=1e-6), (
        f"Con n = 3, J = 0.7, h = 1.3, T = 1.5 y pasos = 6, `curvas` devuelve exacta = {np.round(e, 4).tolist()} "
        f"y trotter = {np.round(t, 4).tolist()}."
    )
