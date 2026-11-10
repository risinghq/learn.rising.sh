import numpy as np
from scipy.linalg import expm
from qiskit.quantum_info import SparsePauliOp

from qgcheck import learner, visible


def reference(n, J, h, dt, pasos):
    terms = [("ZZ", [i, i + 1], J) for i in range(n - 1)]
    terms += [("X", [i], h) for i in range(n)]
    hamiltoniano = SparsePauliOp.from_sparse_list(terms, num_qubits=n).to_matrix()
    magnetizacion = SparsePauliOp.from_sparse_list(
        [("Z", [i], 1 / n) for i in range(n)], num_qubits=n
    ).to_matrix()
    evolucion = expm(-1j * hamiltoniano * dt)
    estado = np.zeros(2**n, dtype=complex)
    estado[0] = 1
    valores = []
    for _ in range(pasos + 1):
        valores.append(float(np.real(np.vdot(estado, magnetizacion @ estado))))
        estado = evolucion @ estado
    return np.array(valores)


def curve(n, J, h, dt, pasos):
    return np.asarray(learner.curva_ideal(n, J, h, dt, pasos), dtype=float)


@visible("la curva exacta contiene el instante inicial y los pasos")
def test_curve():
    got = curve(4, 1.0, 0.5, 0.1, 8)
    want = reference(4, 1.0, 0.5, 0.1, 8)
    assert got.shape == (9,), f"Con pasos = 8, `curva_ideal` devuelve {got.size} puntos."
    assert np.allclose(got, want, atol=1e-10), (
        f"La curva ideal devuelve {np.round(got, 4).tolist()}; "
        f"la referencia es {np.round(want, 4).tolist()}."
    )
    assert not np.allclose(got[1:], 1), (
        "La curva ideal no puede ser constante con un campo transversal no nulo."
    )


def test_other_chain():
    got = curve(3, 0.7, 0.4, 0.2, 4)
    want = reference(3, 0.7, 0.4, 0.2, 4)
    cambios = tuple("igual" if np.isclose(value, got[0]) else "cambia" for value in got[1:])
    assert got.shape == (5,), f"Con n = 3 y pasos = 4, `curva_ideal` devuelve {got.size} valores."
    assert np.allclose(got[1:], want[1:], atol=1e-10) and cambios == ("cambia",) * 4, (
        f"Con n = 3, J = 0.7, h = 0.4 y dt = 0.2, `curva_ideal` devuelve "
        f"el patrón de cambios {cambios} respecto al inicio."
    )
