import functools

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import UnitaryGate

from qgcheck import learner, visible

# Levels 0 and 1 translate the unitary and SWAP separately, using 3 ECRs each.
# Levels 2 and 3 fuse them into one block using 3 ECRs. FakeSherbrooke gives these counts for every
# two-qubit unitary.
EXPECTED = [6, 6, 3, 3]


def unitary_and_swap(seed):
    random = np.random.default_rng(seed)
    q, _ = np.linalg.qr(random.normal(size=(4, 4)) + 1j * random.normal(size=(4, 4)))
    qc = QuantumCircuit(2)
    qc.append(UnitaryGate(q), range(2))
    qc.swap(0, 1)
    return qc


@functools.cache
def counts(seed):
    return list(learner.ecr_por_nivel(unitary_and_swap(seed)))


@visible("devuelve una cuenta por cada nivel, de 0 a 3")
def test_four_counts():
    got = counts(12345)
    assert len(got) == 4, f"`ecr_por_nivel` devuelve {got}: debe tener una cuenta por nivel."


@visible("los niveles altos fusionan la unitaria y el SWAP")
def test_levels_2_and_3_merge():
    got = counts(12345)
    assert len(got) == 4 and got[3] < got[0], f"`ecr_por_nivel` devuelve {got}: el nivel 3 debería usar menos ecr que el 0."


def test_another_unitary():
    got = counts(99)
    assert got == EXPECTED and all(isinstance(n, int) for n in got), f"Con la unitaria de seed = 99, `ecr_por_nivel` devuelve {got}."
