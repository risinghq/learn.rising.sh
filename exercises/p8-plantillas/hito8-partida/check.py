import numpy as np
from scipy.linalg import expm

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.transpiler import generate_preset_pass_manager
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


def circuito(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for a in range(0, n - 1, 2):
            qc.rzz(2 * J * dt, a, a + 1)
        for a in range(1, n - 1, 2):
            qc.rzz(2 * J * dt, a, a + 1)
        for a in range(n):
            qc.rx(2 * h * dt, a)
    return qc


def profundidad(qc):
    return generate_preset_pass_manager(optimization_level=1, backend=FakeFez(), seed_transpiler=1).run(qc).depth()


def leer(n, J, h, dt, pasos):
    got = learner.partida(n, J, h, dt, pasos)
    assert isinstance(got, dict) and {"exacta", "trotter", "profundidad"} <= set(got), (
        f"`partida` debe devolver un diccionario con exacta, trotter y profundidad, y devuelve {got!r}."
    )
    return float(got["exacta"]), float(got["trotter"]), got["profundidad"]


@visible("6 espines y 4 pasos: la magnetización exacta, la de Trotter y la profundidad en FakeFez")
def test_seis_espines():
    e, t, d = leer(6, 1.0, 0.5, 0.2, 4)
    assert np.isclose(e, exacta(6, 1.0, 0.5, 0.2, 4)[-1], atol=1e-6), (
        f"Tu magnetización exacta en t = 0.8 es {e:.4f}; evoluciona |000000⟩ con e^(-iHt), t = dt · pasos."
    )
    assert np.isclose(t, trotter(6, 1.0, 0.5, 0.2, 4)[-1], atol=1e-6), (
        f"Tu magnetización de Trotter es {t:.4f}; mide M en el estado del circuito de 4 pasos."
    )
    assert abs(e - t) < 0.01, f"Exacta {e:.4f} y Trotter {t:.4f} se separan más de 0.01."
    assert d == profundidad(circuito(6, 1.0, 0.5, 0.2, 4)), (
        f"Tu profundidad es {d!r}; transpila el circuito de 4 pasos para FakeFez con optimization_level=1 y seed_transpiler=1."
    )


def test_cuatro_espines():
    e, t, _ = leer(4, 0.8, 1.0, 0.25, 3)
    assert np.isclose(e, exacta(4, 0.8, 1.0, 0.25, 3)[-1], atol=1e-6) and np.isclose(t, trotter(4, 0.8, 1.0, 0.25, 3)[-1], atol=1e-6), (
        f"Con n = 4, J = 0.8, h = 1.0, dt = 0.25 y pasos = 3, `partida` da exacta = {round(e, 4)} y trotter = {round(t, 4)}."
    )
