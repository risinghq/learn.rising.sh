import itertools


def energia(qubo, x):
    return sum(c * __import__("math").prod(x[i] for i in indices) for indices, c in qubo.items())


def elegir_cartera(penalizacion):
    rendimiento = (0.10, 0.08, 0.06, 0.04)
    riesgo = (0.10, 0.08, 0.05, 0.02)
    qubo = {(): penalizacion * 4}
    for i in range(4):
        qubo[(i,)] = -rendimiento[i] + 0.3 * riesgo[i] - 3 * penalizacion
        for j in range(i + 1, 4):
            qubo[(i, j)] = 2 * penalizacion
    return min(itertools.product([0, 1], repeat=4), key=lambda x: energia(qubo, x))
