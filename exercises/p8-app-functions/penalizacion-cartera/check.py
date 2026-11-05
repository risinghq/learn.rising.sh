from qgcheck import learner, visible


@visible("elige exactamente dos activos")
def test_large_penalty():
    penalizacion = 1.0
    got = learner.elegir_cartera(penalizacion)
    assert sum(got) == 2, f"Con penalizacion = {penalizacion}, `elegir_cartera` devuelve {got}."


def test_stronger_penalty():
    penalizacion = 2.0
    got = learner.elegir_cartera(penalizacion)
    assert sum(got) == 2, f"Con penalizacion = {penalizacion}, `elegir_cartera` devuelve {got}."
