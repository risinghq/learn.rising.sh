import numpy as np
from scipy.linalg import expm

import functools

from qgcheck import inside, learner, visible

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


@inside
def modulo_del_estimator():
    return getattr(learner.Estimator, "__module__", "")


@functools.cache
def medida(n, J, h, dt, pasos):
    return np.asarray(learner.medir(n, J, h, dt, pasos), dtype=float)


@visible("4 espines y 3 pasos con el Estimator del lado del cliente en FakeManilaV2")
def test_migrado():
    modulo = modulo_del_estimator()
    assert modulo.startswith("qiskit_ibm_runtime.executor_estimator"), (
        f"Tu `Estimator` viene de `{modulo}`; importa el del lado del cliente."
    )
    got = medida(4, 1.0, 0.5, 0.2, 3)
    ideal = trotter(4, 1.0, 0.5, 0.2, 3)[1:]
    assert got.shape == (3,), f"Con pasos = 3, `medir` devuelve {got.size} valores; mide un circuito por paso, de 1 a 3."
    rms = float(np.sqrt(np.mean((got - ideal) ** 2)))
    assert rms < 0.12, f"Tu curva {np.round(got, 3).tolist()} se aparta de la ideal {np.round(ideal, 3).tolist()} con un RMS de {rms:.3f}."


def test_con_ruido():
    got = medida(4, 1.0, 0.5, 0.2, 3)
    ideal = trotter(4, 1.0, 0.5, 0.2, 3)[1:]
    assert got.shape == (3,), f"Con n = 4, J = 1.0, h = 0.5, dt = 0.2 y pasos = 3, `medir` devuelve {got.size} valores."
    assert np.max(np.abs(got - ideal)) > 1e-3, (
        f"Con n = 4, J = 1.0, h = 0.5, dt = 0.2 y pasos = 3, `medir` devuelve {np.round(got, 4).tolist()}, "
        "sin ruido ni disparos: mide con el Estimator sobre FakeManilaV2."
    )
