import numpy as np
from scipy.linalg import expm

from qiskit.providers.fake_provider import GenericBackendV2

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


def backend(n, fraccional):
    return GenericBackendV2(n, basis_gates=["cz", "rz", "sx", "x"] + (["rx", "rzz"] if fraccional else []), seed=1)


def revisar(n, J, h, dt, pasos, fraccional):
    got = learner.transpilar(n, J, h, dt, pasos, fraccional)
    fuera = unsupported(got, backend(n, fraccional).target)
    assert not fuera, f"Con fraccional = {fraccional}, tu circuito usa operaciones que el backend no ejecuta: {fuera}."
    u = np.asarray(operator(got).data)
    assert igual_salvo_fase(u, trotter_exacto(n, J, h, dt, pasos)), (
        f"Con n = {n}, J = {J}, h = {h}, dt = {dt}, pasos = {pasos} y fraccional = {fraccional}, "
        f"`transpilar` lleva |0…0⟩ a las probabilidades {np.round(np.abs(u[:, 0]) ** 2, 3).tolist()[:4]}…"
    )
    return got


@visible("4 espines y 6 pasos: 36 cz sin fraccionales, 18 rzz y ninguna cz con ellas, la misma evolución y menos duración")
def test_cuatro_espines():
    conv = revisar(4, 1.0, 0.5, 0.2, 6, False)
    frac = revisar(4, 1.0, 0.5, 0.2, 6, True)
    cz = conv.count_ops().get("cz", 0)
    assert cz == 36, f"El circuito convencional tiene {cz} cz; cada rzz se convierte en 2 cz, y 3 enlaces por 6 pasos dan 36."
    ops = dict(frac.count_ops())
    assert ops.get("cz", 0) == 0 and ops.get("rzz", 0) == 18, (
        f"El circuito fraccional tiene las puertas {ops}; cada enlace de cada paso debe quedar como una sola rzz."
    )
    lento = conv.estimate_duration(backend(4, False).target, unit="s")
    rapido = frac.estimate_duration(backend(4, True).target, unit="s")
    assert rapido < lento, f"El fraccional dura {rapido * 1e6:.2f} µs y el convencional {lento * 1e6:.2f} µs."


def test_tres_espines():
    revisar(3, 0.6, 1.1, 0.2, 3, False)
    revisar(3, 0.6, 1.1, 0.2, 3, True)
