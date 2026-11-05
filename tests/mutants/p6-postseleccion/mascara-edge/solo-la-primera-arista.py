import numpy as np


def mascara_edge(meas, meas_ps, aristas):
    meas, meas_ps = np.array(meas, dtype=bool), np.array(meas_ps, dtype=bool)
    paso = meas != meas_ps
    a, b = aristas[0]
    return paso[:, a] | paso[:, b]
