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


PAULIS = [np.eye(2, dtype=complex), X, np.array([[0, -1j], [1j, 0]]), Z]


def despolarizar(rho, n, i, p):
    """El canal despolarizante de dos qubits sobre los espines i e i + 1."""
    giro = sum(
        sobre(n, {i: a, i + 1: b}) @ rho @ sobre(n, {i: a, i + 1: b}) for a in PAULIS for b in PAULIS
    )
    return (1 - p) * rho + p * giro / 16


def ruidosa(n, J, h, dt, pasos, p):
    """Cada rzz son dos cx, y cada cx deja un error despolarizante de probabilidad p en su par."""
    ux = expm(-1j * dt * campo(n, h))
    rho = np.outer(inicial(n), inicial(n))
    M, valores = magnetizacion(n), []
    for k in range(pasos + 1):
        valores.append(float(np.real(np.trace(M @ rho))))
        for i in range(n - 1):
            u = expm(-1j * dt * J * sobre(n, {i: Z, i + 1: Z}))
            rho = despolarizar(despolarizar(u @ rho @ u.conj().T, n, i, p), n, i, p)
        rho = ux @ rho @ ux.conj().T
    return np.array(valores)


def validez(n, J, h, dt, pasos, p, tol):
    lejos = np.abs(ruidosa(n, J, h, dt, pasos, p) - exacta(n, J, h, dt, pasos)) > tol
    return float(np.argmax(lejos) * dt) if lejos.any() else None


def mismo_tiempo(a, b):
    if a is None or b is None:
        return a is None and b is None
    return isinstance(a, (int, float)) and np.isclose(a, b)


@visible("4 espines y p = 0.02: con tol = 0.05 la simulación ruidosa deja de valer en t = 0.1")
def test_cuatro_espines():
    got = learner.tiempo_de_validez(4, 1.0, 1.0, 0.1, 10, 0.02, 0.05)
    assert mismo_tiempo(got, validez(4, 1.0, 1.0, 0.1, 10, 0.02, 0.05)), (
        f"`tiempo_de_validez` devuelve {got!r}, y la curva ruidosa se aparta de la exacta más de 0.05 "
        f"por primera vez en t = {validez(4, 1.0, 1.0, 0.1, 10, 0.02, 0.05)}."
    )


def test_tres_espines():
    got = learner.tiempo_de_validez(3, 0.9, 1.2, 0.35, 6, 0.01, 0.06)
    assert mismo_tiempo(got, validez(3, 0.9, 1.2, 0.35, 6, 0.01, 0.06)), (
        f"Con n = 3, J = 0.9, h = 1.2, dt = 0.35, pasos = 6, p = 0.01 y tol = 0.06, `tiempo_de_validez` devuelve {got!r}."
    )
