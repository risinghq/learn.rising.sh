import math


def tiempo_qpu(eps, va, a=0.004, alfa=0.35, b=60.0):
    return a * math.exp(alfa * va) / eps**2 + b
