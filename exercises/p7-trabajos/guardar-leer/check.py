from qgcheck import learner, visible


@visible("recupera el tipo y los conteos")
def test_roundtrip():
    got = learner.roundtrip(3)
    assert got[0] == "PrimitiveResult" and sum(got[1].values()) == 1024, (
        f"Con seed = 3, `roundtrip` devuelve {got}."
    )


def test_other_seed():
    got = learner.roundtrip(8)
    assert got[0] == "PrimitiveResult" and sum(got[1].values()) == 1024, (
        f"Con seed = 8, `roundtrip` devuelve {got}."
    )
