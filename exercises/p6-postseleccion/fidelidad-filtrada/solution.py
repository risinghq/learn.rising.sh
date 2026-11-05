import numpy as np


def fidelidad(bits, mascara):
    conservados = np.array(bits, dtype=bool)[np.array(mascara, dtype=bool)]
    if len(conservados) == 0:
        return 0.0
    return float((conservados.all(axis=1) | (~conservados).all(axis=1)).mean())
