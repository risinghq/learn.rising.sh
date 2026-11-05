import numpy as np


def fidelidad(bits, mascara):
    b = np.array(bits, dtype=bool)
    return float((b.all(axis=1) | (~b).all(axis=1)).mean())
