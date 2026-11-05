import ast
import itertools


def energia(qubo, x):
    return sum(
        c * __import__("math").prod(x[i] for i in ast.literal_eval(k)) for k, c in qubo.items()
    )


def maximo_corte(aristas, n):
    qubo = {"()": 0.0}
    for i, j in aristas:
        qubo[f"({i},)"] = qubo.get(f"({i},)", 0.0) - 1
        qubo[f"({j},)"] = qubo.get(f"({j},)", 0.0) - 1
        qubo[f"({i}, {j})"] = 2.0
    x = min(itertools.product([0, 1], repeat=n), key=lambda bits: energia(qubo, bits))
    cortadas = sum(x[i] != x[j] for i, j in aristas)
    return qubo, x, cortadas
