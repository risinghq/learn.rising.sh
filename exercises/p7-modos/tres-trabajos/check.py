from qgcheck import learner, visible


@visible("tres trabajos con 4096 disparos")
def test_three_jobs():
    got = learner.trabajos(3)
    assert got == [4096, 4096, 4096], f"Con n_trabajos = 3, devuelve {got}."


def test_two_jobs():
    got = learner.trabajos(2)
    assert got == [4096, 4096], f"Con n_trabajos = 2, devuelve {got}."
