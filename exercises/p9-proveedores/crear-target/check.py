from qgcheck import inside, learner, visible


@inside
def instrucciones():
    return sorted(learner.crear_target([(0, 1), (1, 2)]).operation_names)


@inside
def pares_de_cz(pares):
    return sorted(learner.crear_target(pares).qargs_for_operation_name("cz"))


@visible("el Target tiene las cinco instrucciones")
def test_names():
    got = instrucciones()
    assert got == ["cz", "measure", "rz", "sx", "x"], (
        f"`crear_target` define las instrucciones {got}."
    )


@visible("la CZ une los pares dados")
def test_cz_pairs():
    got = pares_de_cz([(0, 1), (1, 2)])
    assert got == [(0, 1), (1, 2)], (
        f"Con los pares [(0, 1), (1, 2)], `crear_target` pone la CZ en {got}."
    )


def test_cz_only_in_given_pairs():
    got = pares_de_cz([(1, 2)])
    assert got == [(1, 2)], f"Con los pares [(1, 2)], `crear_target` pone la CZ en {got}."
