import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector
from scipy.linalg import expm

from qgcheck import learner, visible


def reference(n, J, h, dt, K):
    observable = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    valores = []
    for k in range(K + 1):
        qc = QuantumCircuit(n)
        for _ in range(k):
            for i in range(n - 1):
                qc.rzz(2 * J * dt, i, i + 1)
            for i in range(n):
                qc.rx(2 * h * dt, i)
        valores.append(
            float(np.real(Statevector.from_instruction(qc).expectation_value(observable)))
        )
    return np.array(valores)


def exacta(n, J, h, dt, K):
    terminos = [("ZZ", [i, i + 1], J) for i in range(n - 1)] + [("X", [i], h) for i in range(n)]
    H = SparsePauliOp.from_sparse_list(terminos, num_qubits=n).to_matrix()
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n).to_matrix()
    psi = np.zeros(2**n, dtype=complex)
    psi[0] = 1
    U = expm(-1j * H * dt)
    valores = []
    for _ in range(K + 1):
        valores.append(float(np.real(np.vdot(psi, M @ psi))))
        psi = U @ psi
    return np.array(valores)


@visible("la curva de Trotter sigue la referencia y tiene K + 1 puntos")
def test_curve():
    got = np.asarray(learner.curva_trotter(4, 1.0, 0.5, 0.1, 8), dtype=float)
    want = reference(4, 1.0, 0.5, 0.1, 8)
    assert got.shape == (9,), f"Con K = 8, `curva_trotter` tiene {got.size} puntos."
    assert np.allclose(got, want, atol=1e-10), (
        f"La curva de Trotter devuelve {np.round(got, 4).tolist()}; "
        f"la referencia es {np.round(want, 4).tolist()}."
    )
    peor = np.max(np.abs(got - exacta(4, 1.0, 0.5, 0.1, 8)))
    assert peor < 0.02, f"Tu curva se aparta de la evolución exacta hasta {peor:.3f}; con dt = 0.1 debe quedar a menos de 0.02."


def test_tres_espines():
    got = np.asarray(learner.curva_trotter(3, 0.7, 1.3, 0.2, 5), dtype=float)
    assert got.shape == (6,) and np.allclose(got, reference(3, 0.7, 1.3, 0.2, 5), atol=1e-8), (
        f"Con n = 3, J = 0.7, h = 1.3, dt = 0.2 y K = 5, `curva_trotter` devuelve {np.round(got, 4).tolist()}."
    )
