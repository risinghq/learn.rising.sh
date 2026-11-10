import functools

import numpy as np
from scipy.linalg import expm

from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime.fake_provider import FakeFez

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
def fez():
    return FakeFez()


def circuito(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
    qc.measure_all()
    return qc


def evaluacion(n, J, h, T, pasos):
    dt = T / pasos
    error = float(np.max(np.abs(exacta(n, J, h, dt, pasos) - trotter(n, J, h, dt, pasos))))
    return error, transpile(circuito(n, J, h, dt, pasos), fez(), optimization_level=1, seed_transpiler=7).depth()


def leer(n, J, h, T, pasos):
    got = learner.evaluar(n, J, h, T, pasos)
    assert isinstance(got, (list, tuple)) and len(got) == 2, f"`evaluar` debe devolver (error_maximo, profundidad) y devuelve {got!r}."
    return float(got[0]), got[1]


@visible("4 espines y T = 2: el error máximo y la profundidad con 6 pasos, y unos pasos con error < 0.02 y profundidad ≤ 200")
def test_cuatro_espines():
    error, profundidad = leer(4, 1.0, 1.0, 2.0, 6)
    ref_error, ref_prof = evaluacion(4, 1.0, 1.0, 2.0, 6)
    assert np.isclose(error, ref_error, atol=1e-6), (
        f"Con 6 pasos tu error máximo es {error:.4f}; compara la exacta y Trotter en todos los instantes k · dt, no solo en T."
    )
    assert profundidad == ref_prof, (
        f"Tu profundidad es {profundidad!r}; mide el circuito de 6 pasos con measure_all transpilado para FakeFez "
        "con optimization_level=1 y seed_transpiler=7."
    )
    pasos = learner.elegir_pasos(4, 1.0, 1.0, 2.0)
    e, d = evaluacion(4, 1.0, 1.0, 2.0, pasos) if isinstance(pasos, int) and pasos > 0 else (1.0, 0)
    assert e < 0.02 and d <= 200, f"`elegir_pasos` elige {pasos!r} pasos: error máximo {e:.4f} y profundidad {d}."


def test_tres_espines():
    error, _ = leer(3, 0.8, 1.2, 1.5, 4)
    assert np.isclose(error, evaluacion(3, 0.8, 1.2, 1.5, 4)[0], atol=1e-6), (
        f"Con n = 3, J = 0.8, h = 1.2, T = 1.5 y pasos = 4, `evaluar` da un error máximo de {round(error, 4)}."
    )
