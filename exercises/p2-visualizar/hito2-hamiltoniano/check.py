import numpy as np

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


def matriz(n, J, h):
    return np.asarray(learner.hamiltoniano(n, J, h).to_matrix())


def diagonal(m):
    return np.round(np.real(np.diag(m)), 3).tolist()


@visible("con 5 espines, la matriz es J·ΣZᵢZᵢ₊₁ + h·ΣXᵢ de la cadena abierta")
def test_cinco():
    got = matriz(5, 1.0, 0.5)
    want = enlaces(5, 1.0) + campo(5, 0.5)
    assert got.shape == want.shape, f"Con n = 5, `hamiltoniano` actúa sobre {int(np.log2(len(got)))} qubits."
    assert np.allclose(got, want), (
        f"Con n = 5, J = 1.0 y h = 0.5, la diagonal de tu Hamiltoniano empieza {diagonal(got)[:8]} "
        f"y la de la cadena es {diagonal(want)[:8]}."
    )


def test_tres_con_signo():
    got = matriz(3, -0.3, 1.2)
    assert np.allclose(got, enlaces(3, -0.3) + campo(3, 1.2)), (
        f"Con n = 3, J = -0.3 y h = 1.2, la diagonal de `hamiltoniano` es {diagonal(got)}."
    )
