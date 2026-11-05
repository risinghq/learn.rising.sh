import math


def precision_alcanzable(t_max, va, a=0.004, alfa=0.35, b=60.0):
    if t_max <= b:
        raise ValueError("el presupuesto no cubre el coste fijo")
    return math.sqrt(a * math.exp(alfa * va) / (t_max - b))
