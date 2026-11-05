import numpy as np


def mascara_node(meas, meas_ps):
    # Un bit pasó el control si meas != meas_ps.
    meas, meas_ps = np.array(meas, dtype=bool), np.array(meas_ps, dtype=bool)
    return np.ones(len(meas), dtype=bool)
