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


def de_cuentas(m, n, disparos):
    """Una media de ±1 sobre n·disparos lecturas es un entero dividido entre n·disparos."""
    return isinstance(m, float) and np.isclose(m * n * disparos, round(m * n * disparos), atol=1e-6)


@visible("3 espines y 2 pasos con el ruido de FakeManilaV2: la medida sale de las cuentas y el ruido la sesga")
def test_tres_espines():
    got = learner.magnetizacion_medida(3, 1.0, 1.0, 0.25, 2, 4000)
    ideal = trotter(3, 1.0, 1.0, 0.25, 2)[-1]
    assert de_cuentas(got, 3, 4000), f"`magnetizacion_medida` devuelve {got!r}, que no es una media de cuentas de 4000 disparos."
    assert abs(got - ideal) < 0.15, f"Tu medida {got:.4f} queda lejos de Trotter sin ruido, {ideal:.4f}."
    assert abs(got - exacta(3, 1.0, 1.0, 0.25, 2)[-1]) > 0.03, (
        f"Tu medida {got:.4f} está a menos de 0.03 de la exacta, {exacta(3, 1.0, 1.0, 0.25, 2)[-1]:.4f}: "
        "con el ruido de FakeManilaV2 y la semilla 3 tiene que notarse el sesgo."
    )


def test_otro_campo():
    got = learner.magnetizacion_medida(3, 0.8, 1.2, 0.3, 3, 4000)
    assert de_cuentas(got, 3, 4000) and abs(got - trotter(3, 0.8, 1.2, 0.3, 3)[-1]) < 0.15 and (
        abs(got - exacta(3, 0.8, 1.2, 0.3, 3)[-1]) > 0.03
    ), f"Con n = 3, J = 0.8, h = 1.2, dt = 0.3, pasos = 3 y disparos = 4000, `magnetizacion_medida` devuelve {got!r}."
