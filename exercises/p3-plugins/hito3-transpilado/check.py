import numpy as np
from qiskit_ibm_runtime.fake_provider import FakeFez
from scipy.linalg import expm

from qgcheck import learner, operator, unsupported, visible

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


def trotter_exacto(n, J, h, dt, pasos):
    paso = expm(-1j * dt * campo(n, h)) @ expm(-1j * dt * enlaces(n, J))
    return np.linalg.matrix_power(paso, pasos)


def igual_salvo_fase(a, b):
    return a.shape == b.shape and np.isclose(abs(np.vdot(a, b)) / len(a), 1, atol=1e-6)


def probabilidades(u):
    return np.round(np.abs(u[:, 0]) ** 2, 3).tolist()


@visible("4 espines y 2 pasos: solo puertas de FakeFez, 12 cz y la misma evolución")
def test_fez():
    got = learner.circuito(4, 1.0, 0.5, 0.1, 2)
    fuera = unsupported(got, FakeFez().target)
    assert not fuera, f"Tu circuito usa operaciones que FakeFez no ejecuta: {fuera}."
    assert got.count_ops().get("cz", 0) == 12, (
        f"Tu circuito tiene {got.count_ops().get('cz', 0)} cz; cada rzz entre vecinos se convierte en 2 cz, "
        "así que 3 enlaces por 2 pasos dan 12."
    )
    u = np.asarray(operator(got).data)
    assert igual_salvo_fase(u, trotter_exacto(4, 1.0, 0.5, 0.1, 2)), (
        f"Con J = 1.0, h = 0.5 y dt = 0.1, tu circuito lleva |0000⟩ a las probabilidades {probabilidades(u)[:4]}…, "
        f"y dos pasos de Trotter dan {probabilidades(trotter_exacto(4, 1.0, 0.5, 0.1, 2))[:4]}…"
    )


def test_otros_parametros():
    u = np.asarray(operator(learner.circuito(3, 0.7, 1.3, 0.15, 3)).data)
    assert igual_salvo_fase(u, trotter_exacto(3, 0.7, 1.3, 0.15, 3)), (
        f"Con n = 3, J = 0.7, h = 1.3, dt = 0.15 y pasos = 3, `circuito` lleva |000⟩ a las probabilidades {probabilidades(u)}."
    )
