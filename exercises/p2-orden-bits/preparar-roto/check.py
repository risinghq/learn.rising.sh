import numpy as np
from qiskit.quantum_info import Statevector

from qgcheck import learner, visible


def amplitude_at(k, n):
    qc = learner.preparar(k, n)
    assert qc.num_qubits == n, f"Con k = {k} y n = {n}, el circuito tiene {qc.num_qubits} qubits."
    return Statevector(qc).data


@visible("preparar(5, 4) deja la amplitud en el índice 5")
def test_example():
    vector = amplitude_at(5, 4)
    assert np.isclose(abs(vector[5]), 1), f"Con k = 5 y n = 4 la amplitud está en el índice {int(np.argmax(abs(vector)))}."


@visible("preparar(1, 3) deja la amplitud en el índice 1")
def test_one():
    vector = amplitude_at(1, 3)
    assert np.isclose(abs(vector[1]), 1), f"Con k = 1 y n = 3 la amplitud está en el índice {int(np.argmax(abs(vector)))}."


def test_other_sizes():
    for n in (3, 6):
        for k in range(2**n):
            vector = amplitude_at(k, n)
            assert np.isclose(abs(vector[k]), 1), f"Con k = {k} y n = {n}, la amplitud está en el índice {int(np.argmax(abs(vector)))}."
