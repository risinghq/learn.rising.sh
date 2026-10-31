import numpy as np

from qgcheck import counts, learner, state, visible

BELL = np.array([1, 0, 0, 1]) / np.sqrt(2)


@visible("los qubits salen siempre iguales")
def test_counts():
    got = sorted(counts(learner.bell))
    assert got == ["00", "11"], f"Salen {got}. Busca que solo aparezcan 00 y 11."


@visible("el estado es (|00⟩ + |11⟩)/√2")
def test_state():
    assert state(learner.bell).equiv(BELL), "El estado antes de medir no es (|00⟩ + |11⟩)/√2."


def test_balanced():
    got = counts(learner.bell, shots=4096, seed=99)
    low, high = 2048 - 256, 2048 + 256
    assert low <= got.get("00", 0) <= high and low <= got.get("11", 0) <= high, (
        f"Con seed = 99 y 4096 repeticiones salen {dict(sorted(got.items()))}.")
