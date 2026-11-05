from qgcheck import learner, visible


@visible("reparte veinte circuitos en cinco grupos")
def test_twenty():
    circuitos = list(range(20))
    got = learner.partir(circuitos)
    assert got == [list(range(i, i + 4)) for i in range(0, 20, 4)], (
        f"Con circuitos = {circuitos}, partir devuelve {got}."
    )


def test_eight():
    circuitos = list(range(8))
    got = learner.partir(circuitos)
    assert got == [[0, 1, 2, 3], [4, 5, 6, 7]], (
        f"Con circuitos = {circuitos}, partir devuelve {got}."
    )
