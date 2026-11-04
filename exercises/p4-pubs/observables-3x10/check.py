import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp

from qgcheck import learner, visible

PAULIS = ["ZZZ", "XXX", "YYY"]


def reference():
    circ = QuantumCircuit(3)
    circ.ry(Parameter("a"), 0)
    circ.cx(0, 1)
    circ.cx(1, 2)
    values = np.linspace(0, np.pi, 10)[:, None]
    return np.array(
        [StatevectorEstimator().run([(circ, SparsePauliOp(p), values)]).result()[0].data.evs for p in PAULIS]
    )


@visible("una fila por observable y una columna por valor")
def test_shape():
    shape = learner.evs_barrido.shape
    assert shape == (3, 10), f"`evs_barrido` tiene la forma {shape}; debe tener una fila por observable y una columna por valor de `a`."


def test_rows_follow_the_observables():
    want = reference()
    got = np.round(learner.evs_barrido, 3)
    for row, pauli in enumerate(PAULIS):
        assert np.allclose(got[row], want[row], atol=1e-3), (
            f"La fila {row} de `evs_barrido` vale {got[row].tolist()}; no es la del observable {pauli}.")
