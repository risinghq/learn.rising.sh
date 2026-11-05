from math import pi

from qgcheck import learner, visible


@visible("un múltiplo de pi/2 acorta la descomposición")
def test_special_angle():
    got = learner.conteos_con_angulo(pi / 2)
    assert got < 24, f"Con theta_zz = {pi / 2}, devuelve {got}."


def test_another_special_angle():
    got = learner.conteos_con_angulo(3 * pi / 2)
    assert got < 24, f"Con theta_zz = {3 * pi / 2}, devuelve {got}."
