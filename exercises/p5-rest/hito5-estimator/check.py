import numpy as np
from scipy.linalg import expm

import functools

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


@functools.cache
def medida(n, J, h, dt, pasos, disparos):
    return np.asarray(learner.ejecutar(n, J, h, dt, pasos, disparos), dtype=float)


@visible("3 espines y 4 circuitos con ruido de FakeManilaV2: la curva medida sigue a la ideal")
def test_medida():
    got = medida(3, 1.0, 1.0, 0.25, 4, 2000)
    ideal = trotter(3, 1.0, 1.0, 0.25, 4)[1:]
    assert got.shape == (4,), f"Con pasos = 4, `ejecutar` devuelve {got.size} valores; debe devolver uno por circuito, de 1 a 4 pasos."
    rms = float(np.sqrt(np.mean((got - ideal) ** 2)))
    assert rms < 0.12, (
        f"Tu curva {np.round(got, 3).tolist()} se aparta de la ideal {np.round(ideal, 3).tolist()} con un RMS de {rms:.3f}."
    )


def test_con_ruido():
    got = medida(3, 1.0, 1.0, 0.25, 4, 2000)
    ideal = trotter(3, 1.0, 1.0, 0.25, 4)[1:]
    assert got.shape == (4,) and np.max(np.abs(got - ideal)) > 1e-3, (
        f"Con n = 3, J = 1.0, h = 1.0, dt = 0.25, pasos = 4 y disparos = 2000, `ejecutar` devuelve "
        f"{np.round(got, 4).tolist()}, sin ruido ni disparos: ejecuta en FakeManilaV2 con el Estimator."
    )
