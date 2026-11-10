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
def medida():
    return np.asarray(learner.lote(3, 0.8, 1.2, 0.25, 2), dtype=float)


@visible("3 espines y 2 trabajos en un lote de FakeBelemV2: cada medida queda a menos de 0.15 del valor sin ruido")
def test_lote():
    got = medida()
    ideal = trotter(3, 0.8, 1.2, 0.25, 2)[1:]
    assert got.shape == (2,), f"Con pasos = 2, `lote` devuelve {got.size} valores; debe enviar un trabajo por paso, de 1 a 2."
    peor = float(np.max(np.abs(got - ideal)))
    assert peor < 0.15, (
        f"Tus medidas {np.round(got, 3).tolist()} se apartan de las ideales {np.round(ideal, 3).tolist()} hasta {peor:.3f}."
    )


def test_con_ruido():
    got = medida()
    ideal = trotter(3, 0.8, 1.2, 0.25, 2)[1:]
    assert got.shape == (2,), f"Con n = 3, J = 0.8, h = 1.2, dt = 0.25 y pasos = 2, `lote` devuelve {got.size} valores."
    assert np.max(np.abs(got - ideal)) > 1e-3, (
        f"Con n = 3, J = 0.8, h = 1.2, dt = 0.25 y pasos = 2, `lote` devuelve {np.round(got, 4).tolist()}, "
        "sin ruido ni disparos: mide con el Estimator dentro del Batch de FakeBelemV2."
    )
