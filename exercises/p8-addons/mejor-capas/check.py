from qgcheck import learner, visible


@visible("elige capas para tres límites")
def test_limits():
    limites = (10, 30, 100)
    got = {limite: learner.mejor_k(limite) for limite in limites}
    assert got == {10: 0, 30: 3, 100: 5}, f"Con límites = {limites}, `mejor_k` devuelve {got}."


def test_small_limit():
    limite = 1
    got = learner.mejor_k(limite)
    assert got == 0, f"Con límite = {limite}, `mejor_k` devuelve {got}."
