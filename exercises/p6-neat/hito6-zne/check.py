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


def capa(rho, n, J, h, dt, p, inversa):
    """Un paso de Trotter, o su inverso, con dos errores despolarizantes tras cada rzz."""
    ux = expm(-1j * dt * campo(n, h))
    signo, orden = (1, range(n - 1)) if not inversa else (-1, reversed(range(n - 1)))
    if inversa:
        rho = ux.conj().T @ rho @ ux
    for i in orden:
        u = expm(-1j * signo * dt * J * sobre(n, {i: Z, i + 1: Z}))
        rho = despolarizar(despolarizar(u @ rho @ u.conj().T, n, i, p), n, i, p)
    if not inversa:
        rho = ux @ rho @ ux.conj().T
    return rho


def plegados(n, J, h, dt, pasos, p):
    """⟨M⟩ con los factores de ruido 1, 3 y 5: U, U U† U y U U† U U† U."""
    valores = []
    for k in (0, 1, 2):
        rho = np.outer(inicial(n), inicial(n))
        for tramo in [False] + [True, False] * k:
            for _ in range(pasos):
                rho = capa(rho, n, J, h, dt, p, tramo)
        valores.append(float(np.real(np.trace(magnetizacion(n) @ rho))))
    return valores


def mitigado(n, J, h, dt, pasos, p):
    _, ordenada = np.polyfit([1, 3, 5], np.log(plegados(n, J, h, dt, pasos, p)), 1)
    return float(np.exp(ordenada))


def leer(n, J, h, dt, pasos, p):
    got = learner.zne(n, J, h, dt, pasos, p)
    assert isinstance(got, (list, tuple)) and len(got) == 2, f"`zne` debe devolver (crudo, mitigado) y devuelve {got!r}."
    return float(got[0]), float(got[1])


@visible("3 espines y p = 0.03: el valor crudo, la extrapolación a ruido cero y la mejora")
def test_tres_espines():
    crudo, zne = leer(3, 1.0, 1.0, 0.25, 2, 0.03)
    assert np.isclose(crudo, plegados(3, 1.0, 1.0, 0.25, 2, 0.03)[0], atol=1e-6), (
        f"Tu valor crudo es {crudo:.4f} y el circuito sin plegar, con p = 0.03 en cada cx, da "
        f"{plegados(3, 1.0, 1.0, 0.25, 2, 0.03)[0]:.4f}."
    )
    ideal = trotter(3, 1.0, 1.0, 0.25, 2)[-1]
    assert abs(zne - ideal) < abs(crudo - ideal), (
        f"La extrapolación {zne:.4f} no se acerca a Trotter sin ruido ({ideal:.4f}) más que el valor crudo {crudo:.4f}. "
        "Si los tres factores dan lo mismo, el transpilador canceló U† U: separa las mitades con barreras."
    )
    assert np.isclose(zne, mitigado(3, 1.0, 1.0, 0.25, 2, 0.03), atol=1e-5), (
        f"Tu extrapolación es {zne:.4f}; la exponencial que pasa por los factores 1, 3 y 5 da "
        f"{mitigado(3, 1.0, 1.0, 0.25, 2, 0.03):.4f} en el factor 0."
    )


def test_otro_campo():
    _, zne = leer(3, 0.8, 0.6, 0.3, 2, 0.05)
    assert np.isclose(zne, mitigado(3, 0.8, 0.6, 0.3, 2, 0.05), atol=1e-5), (
        f"Con n = 3, J = 0.8, h = 0.6, dt = 0.3, pasos = 2 y p = 0.05, `zne` extrapola {round(zne, 4)}."
    )
