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


PAULIS = [np.eye(2, dtype=complex), X, np.array([[0, -1j], [1j, 0]]), Z]


def despolarizar(rho, n, i, p):
    """El canal despolarizante de dos qubits sobre los espines i e i + 1."""
    giro = sum(
        sobre(n, {i: a, i + 1: b}) @ rho @ sobre(n, {i: a, i + 1: b}) for a in PAULIS for b in PAULIS
    )
    return (1 - p) * rho + p * giro / 16


def ruidosa(n, J, h, dt, pasos, p):
    """Cada rzz son dos cx, y cada cx deja un error despolarizante de probabilidad p en su par."""
    ux = expm(-1j * dt * campo(n, h))
    rho = np.outer(inicial(n), inicial(n))
    M, valores = magnetizacion(n), []
    for k in range(pasos + 1):
        valores.append(float(np.real(np.trace(M @ rho))))
        for i in range(n - 1):
            u = expm(-1j * dt * J * sobre(n, {i: Z, i + 1: Z}))
            rho = despolarizar(despolarizar(u @ rho @ u.conj().T, n, i, p), n, i, p)
        rho = ux @ rho @ ux.conj().T
    return np.array(valores)


def leer(n, J, h, dt, pasos, p):
    return np.asarray(learner.curva_ruidosa(n, J, h, dt, pasos, p), dtype=float)


@visible("4 espines, 6 pasos y p = 0.02: la curva coincide con el modelo de ruido y se aparta de la ideal")
def test_cuatro_espines():
    got = leer(4, 1.0, 1.0, 0.1, 6, 0.02)
    assert got.shape == (7,), f"Con pasos = 6, tu curva tiene {got.size} puntos; debe tener 7, de t = 0 a t = 0.6."
    assert np.max(np.abs(got - trotter(4, 1.0, 1.0, 0.1, 6))) > 0.02, (
        f"Tu curva {np.round(got, 3).tolist()} es la de Trotter sin ruido. Revisa que el modelo "
        "ponga el error en las cx y que simules el circuito ya transpilado a cx."
    )
    assert np.allclose(got, ruidosa(4, 1.0, 1.0, 0.1, 6, 0.02), atol=1e-6), (
        f"Tu curva es {np.round(got, 4).tolist()} y con un despolarizante de p = 0.02 en cada cx sale "
        f"{np.round(ruidosa(4, 1.0, 1.0, 0.1, 6, 0.02), 4).tolist()}."
    )


def test_tres_espines():
    got = leer(3, 0.7, 0.9, 0.2, 4, 0.05)
    assert got.shape == (5,) and np.allclose(got, ruidosa(3, 0.7, 0.9, 0.2, 4, 0.05), atol=1e-6), (
        f"Con n = 3, J = 0.7, h = 0.9, dt = 0.2, pasos = 4 y p = 0.05, `curva_ruidosa` devuelve {np.round(got, 4).tolist()}."
    )
