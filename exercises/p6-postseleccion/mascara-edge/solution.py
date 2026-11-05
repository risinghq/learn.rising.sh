import numpy as np


def mascara_edge(meas, meas_ps, aristas):
    meas, meas_ps = np.array(meas, dtype=bool), np.array(meas_ps, dtype=bool)
    paso = meas != meas_ps
    conserva = np.ones(len(meas), dtype=bool)
    for a, b in aristas:
        conserva &= paso[:, a] | paso[:, b]
    return conserva
