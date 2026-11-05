from qgcheck import learner, visible


@visible("reúne cuatro referencias")
def test_four_tasks():
    from qiskit.circuit.random import random_circuit

    circuitos = [random_circuit(3, 2, seed=seed) for seed in range(4)]
    got = learner.profundidades(circuitos)
    assert len(got) == 4 and all(isinstance(d, int) and d > 0 for d in got), (
        f"Con circuitos = 4, `profundidades` devuelve {got}."
    )


def test_two_tasks():
    from qiskit.circuit.random import random_circuit

    circuitos = [random_circuit(4, 2, seed=seed) for seed in range(2)]
    got = learner.profundidades(circuitos)
    assert len(got) == 2 and all(d > 0 for d in got), (
        f"Con circuitos = 2, `profundidades` devuelve {got}."
    )
