from qgcheck import learner, visible


@visible("absorbe cuatro capas")
def test_four_layers():
    got = learner.retropropaga(4)
    assert got[0] == 64 and got[1] == 8 and abs(got[2]) <= 1, (
        f"Con capas_absorbidas = 4, `retropropaga` devuelve {got}."
    )


def test_two_layers():
    got = learner.retropropaga(2)
    assert got[0] == 16 and got[1] == 10 and abs(got[2]) <= 1, (
        f"Con capas_absorbidas = 2, `retropropaga` devuelve {got}."
    )
