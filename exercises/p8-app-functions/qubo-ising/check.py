import ast

import numpy as np

from qgcheck import inside, learner, visible


@inside
def energias(qubo):
    hamiltoniano, constante = learner.qubo_a_ising(qubo, 3)
    diagonal = np.real(np.diag(hamiltoniano.to_matrix()))
    directas = [
        sum(
            coef * np.prod([bits[i] for i in ast.literal_eval(indices)])
            for indices, coef in qubo.items()
        )
        for k in range(8)
        for bits in [[(k >> i) & 1 for i in range(3)]]
    ]
    return constante, diagonal.tolist(), directas


@visible("coinciden las ocho energías")
def test_linear_and_quadratic_terms():
    qubo = {"()": 0.5, "(0,)": -1.0, "(1,)": 0.25, "(0, 1)": 2.0}
    constante, diagonal, directas = energias(qubo)
    assert np.allclose(np.array(diagonal) + constante, directas), (
        f"Con qubo = {qubo}, `qubo_a_ising` devuelve constante = {constante}."
    )


def test_other_qubo():
    qubo = {"()": -0.2, "(2,)": 1.5, "(0, 2)": -0.8}
    constante, diagonal, directas = energias(qubo)
    assert np.allclose(np.array(diagonal) + constante, directas), (
        f"Con qubo = {qubo}, `qubo_a_ising` devuelve constante = {constante}."
    )
