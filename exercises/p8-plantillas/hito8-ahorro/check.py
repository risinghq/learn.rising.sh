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
from qiskit_addon_obp import backpropagate
from qiskit_addon_obp.utils.simplify import OperatorBudget
from qiskit_addon_utils.slicing import slice_by_gate_types


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


def capas_restantes(n, J, h, dt, pasos, limite):
    from qiskit.quantum_info import SparsePauliOp

    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    _, resto, _ = backpropagate(M, slice_by_gate_types(circuito(n, J, h, dt, pasos)), operator_budget=OperatorBudget(max_paulis=limite))
    return len(resto)


def leer(n, J, h, dt, pasos, limite):
    got = learner.ahorro(n, J, h, dt, pasos, limite)
    assert isinstance(got, (list, tuple)) and len(got) == 2 and isinstance(got[0], QuantumCircuit), (
        f"`ahorro` debe devolver (corto, observable) y devuelve {got!r}."
    )
    corto, observable = got
    return corto, observable, float(np.real(Statevector(corto).expectation_value(observable)))


@visible("6 espines, 4 pasos y 100 términos: OBP se detiene solo, conserva el valor y baja la profundidad")
def test_seis_espines():
    corto, observable, valor = leer(6, 1.0, 0.5, 0.2, 4, 100)
    assert len(observable) <= 100, (
        f"Tu observable tiene {len(observable)} términos con limite = 100; pasa operator_budget=OperatorBudget(max_paulis=limite)."
    )
    assert np.isclose(valor, trotter(6, 1.0, 0.5, 0.2, 4)[-1], atol=1e-8), (
        f"El circuito corto y su observable dan {valor:.6f}, y el circuito completo da {trotter(6, 1.0, 0.5, 0.2, 4)[-1]:.6f}."
    )
    d = profundidad(corto)
    assert d < profundidad(circuito(6, 1.0, 0.5, 0.2, 4)), f"Tu circuito corto tiene profundidad {d} en FakeFez, la misma que el completo."


def test_limite_bajo():
    corto, observable, valor = leer(4, 0.8, 1.0, 0.25, 3, 20)
    assert len(observable) <= 20 and np.isclose(valor, trotter(4, 0.8, 1.0, 0.25, 3)[-1], atol=1e-8), (
        f"Con n = 4, J = 0.8, h = 1.0, dt = 0.25, pasos = 3 y limite = 20, `ahorro` deja {len(observable)} términos "
        f"y el valor {valor:.6f}."
    )
