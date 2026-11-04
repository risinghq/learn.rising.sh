from qgcheck import learner, visible


def shapes(first, second):
    return [list(first.shape), list(second.shape)]


@visible("tu apuesta son las formas de uno_a_uno y de producto")
def test_bet():
    bet = learner.prediccion
    try:
        got = [list(s) for s in bet]
    except TypeError:
        got = None
    assert got == shapes(learner.uno_a_uno, learner.producto), (
        "Tu apuesta no coincide con las formas de `evs`. Ten en cuenta que el broadcasting empareja los ejes desde el último: (5,) con (5,) se empareja uno a uno, y (4, 1) con (1, 6) crece a un eje de cada tamaño.")


def test_same_sweeps():
    got = shapes(learner.uno_a_uno, learner.producto)
    assert got == [[5], [4, 6]], f"`uno_a_uno` y `producto` tienen ahora las formas {got}; los barridos de la lección cambiaron."
