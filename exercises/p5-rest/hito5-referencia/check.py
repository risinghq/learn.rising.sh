import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector

from qgcheck import learner, visible


def reference(n, J, h, dt, pasos):
    observable = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    valores = []
    for k in range(pasos + 1):
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


@visible("la referencia incluye el estado inicial y los valores posteriores")
def test_reference():
    got = np.asarray(learner.magnetizacion_referencia(4, 1.0, 0.5, 0.1, 4), dtype=float)
    want = reference(4, 1.0, 0.5, 0.1, 4)
    assert got.shape == (5,), (
        f"Con pasos = 4, `magnetizacion_referencia` devuelve {got.size} valores."
    )
    assert np.allclose(got, want, atol=1e-10), (
        f"La referencia devuelve {np.round(got, 4).tolist()}; "
        f"la curva esperada es {np.round(want, 4).tolist()}."
    )
    assert not np.allclose(got[1:], 1), (
        "Con h no nulo, la referencia no puede quedarse constante en uno."
    )


def test_other_chain():
    got = learner.magnetizacion_referencia(3, 0.7, 1.3, 0.15, 3)
    assert np.allclose(np.asarray(got, dtype=float), reference(3, 0.7, 1.3, 0.15, 3), atol=1e-10), (
        f"Con n = 3, J = 0.7, h = 1.3, dt = 0.15 y pasos = 3, "
        f"`magnetizacion_referencia` devuelve {got}."
    )
