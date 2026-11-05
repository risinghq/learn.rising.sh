import numpy as np


def mascara_node(meas, meas_ps):
    meas, meas_ps = np.array(meas, dtype=bool), np.array(meas_ps, dtype=bool)
    return (meas == meas_ps).all(axis=1)
