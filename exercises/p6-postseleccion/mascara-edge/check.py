from qgcheck import inside, learner, visible

LINEA = [(0, 1), (1, 2), (2, 3)]
MEAS = [[0, 0, 0, 0], [1, 1, 1, 1], [0, 1, 0, 0]]
PS = [[1, 1, 1, 1], [0, 0, 1, 0], [1, 0, 1, 1]]
MEAS_2 = [[0, 0, 0, 0]] * 4
PS_2 = [[1, 0, 0, 1], [0, 1, 1, 0], [1, 1, 0, 0], [0, 1, 0, 1]]


@inside
def conservados(meas, meas_ps):
    mascara = learner.mascara_edge(meas, meas_ps, [(0, 1), (1, 2), (2, 3)])
    return [i for i, k in enumerate(mascara) if k]


@visible("conserva el disparo si cada arista tiene un bit que pasó")
def test_every_edge_has_a_pass():
    got = conservados(MEAS, PS)
    assert got == [0, 1, 2], f"Con meas_ps = {PS}, `mascara_edge` conserva los disparos {got}."


def test_an_edge_without_a_pass():
    got = conservados(MEAS_2, PS_2)
    assert got == [1, 3], f"Con meas_ps = {PS_2}, `mascara_edge` conserva los disparos {got}."
