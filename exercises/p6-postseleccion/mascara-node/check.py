from qgcheck import inside, learner, visible

MEAS = [[0, 0, 0, 0], [1, 1, 1, 1], [0, 1, 0, 0]]
PS = [[1, 1, 1, 1], [0, 0, 1, 0], [1, 0, 1, 1]]
MEAS_2 = [[0, 1], [1, 0]]
PS_2 = [[0, 1], [1, 1]]


@inside
def conservados(meas, meas_ps):
    mascara = learner.mascara_node(meas, meas_ps)
    return [i for i, k in enumerate(mascara) if k]


@visible("conserva los disparos cuyos cuatro bits pasaron")
def test_all_pass():
    got = conservados(MEAS, PS)
    assert got == [0, 2], f"Con meas_ps = {PS}, `mascara_node` conserva los disparos {got}."


def test_none_passes():
    got = conservados(MEAS_2, PS_2)
    assert got == [], f"Con meas_ps = {PS_2}, `mascara_node` conserva los disparos {got}."
