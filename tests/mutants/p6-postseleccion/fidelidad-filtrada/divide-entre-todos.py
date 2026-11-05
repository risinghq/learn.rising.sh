import numpy as np


def fidelidad(bits, mascara):
    b = np.array(bits, dtype=bool)
    ok = b.all(axis=1) | (~b).all(axis=1)
    return float((ok & np.array(mascara, dtype=bool)).mean())
