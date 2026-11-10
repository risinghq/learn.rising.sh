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
    return np.isclose(m * n * disparos, round(m * n * disparos), atol=1e-6)


@visible("4 espines, 4 pasos y 4000 disparos: la magnetización desde los conteos del Sampler en FakeManilaV2")
def test_cuatro_espines():
    got = float(learner.magnetizacion_conteos(4, 1.0, 0.5, 0.2, 4, 4000))
    assert de_cuentas(got, 4, 4000), f"Tu magnetización {got!r} no sale de 4000 disparos de 4 bits: cuéntala desde los conteos."
    ideal = trotter(4, 1.0, 0.5, 0.2, 4)[-1]
    assert abs(got - ideal) < 0.15, f"Tu magnetización es {got:.4f} y la ideal es {ideal:.4f}: revisa el signo de cada bit."
    assert abs(got - ideal) > 0.05, f"Tu magnetización {got:.4f} casi no tiene ruido; ejecuta el Sampler sobre FakeManilaV2."


def test_tres_espines():
    got = float(learner.magnetizacion_conteos(3, 0.8, 1.2, 0.3, 3, 4000))
    ideal = trotter(3, 0.8, 1.2, 0.3, 3)[-1]
    assert de_cuentas(got, 3, 4000) and 0.03 < abs(got - ideal) < 0.15, (
        f"Con n = 3, J = 0.8, h = 1.2, dt = 0.3, pasos = 3 y disparos = 4000, `magnetizacion_conteos` devuelve {round(got, 4)}."
    )
