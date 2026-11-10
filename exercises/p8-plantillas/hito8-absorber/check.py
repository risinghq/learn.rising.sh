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
    got = learner.absorber(n, J, h, dt, pasos)
    assert isinstance(got, (list, tuple)) and len(got) == 3, f"`absorber` debe devolver (k, corto, observable) y devuelve {got!r}."
    k, corto, observable = got
    assert isinstance(corto, QuantumCircuit) and observable is not None, (
        f"`absorber` devuelve corto = {corto!r} y observable = {observable!r}; deben ser un circuito y un SparsePauliOp."
    )
    valor = float(np.real(Statevector(corto).expectation_value(observable)))
    return k, corto, observable, valor


@visible("6 espines y 4 pasos: OBP absorbe k capas finales sin cambiar el valor, con 100 términos o menos y 3/4 de la profundidad")
def test_seis_espines():
    k, corto, observable, valor = leer(6, 1.0, 0.5, 0.2, 4)
    assert np.isclose(valor, trotter(6, 1.0, 0.5, 0.2, 4)[-1], atol=1e-8), (
        f"Con k = {k!r}, el circuito corto y su observable dan {valor:.6f}, y el circuito completo da "
        f"{trotter(6, 1.0, 0.5, 0.2, 4)[-1]:.6f}. El circuito corto son las capas que no absorbiste, en su orden."
    )
    assert len(observable) <= 100, f"Con k = {k!r}, tu observable tiene {len(observable)} términos."
    d = profundidad(corto)
    assert d <= 0.75 * profundidad(circuito(6, 1.0, 0.5, 0.2, 4)), (
        f"Con k = {k!r}, tu circuito corto tiene profundidad {d} en FakeFez; necesita bajar a 3/4 de la del completo."
    )


def test_cuatro_espines():
    k, corto, observable, valor = leer(4, 0.8, 1.0, 0.25, 3)
    assert np.isclose(valor, trotter(4, 0.8, 1.0, 0.25, 3)[-1], atol=1e-8), (
        f"Con n = 4, J = 0.8, h = 1.0, dt = 0.25 y pasos = 3, `absorber` elige k = {k!r} y el circuito corto da {valor:.6f}."
    )
