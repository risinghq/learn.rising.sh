from qgcheck import learner, visible


@visible("una profundidad por circuito")
def test_three_circuits():
    from qiskit.circuit.random import random_circuit

    circuitos = [random_circuit(3, 2, seed=seed) for seed in range(3)]
    got = learner.ejecutar(circuitos)
    assert len(got) == 3 and all(isinstance(d, int) and d > 0 for d in got), (
        f"Con circuitos = {len(circuitos)}, `ejecutar` devuelve {got}."
    )


def test_four_circuits():
    from qiskit.circuit.random import random_circuit

    circuitos = [random_circuit(4, 2, seed=seed) for seed in range(4)]
    got = learner.ejecutar(circuitos)
    assert len(got) == len(circuitos) and all(d > 0 for d in got), (
        f"Con circuitos = {len(circuitos)}, `ejecutar` devuelve {got}."
    )
