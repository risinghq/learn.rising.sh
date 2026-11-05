import math

from qgcheck import learner, visible


@visible("dos distribuciones iguales o sin cadenas en común")
def test_extremes():
    for a, b, esperado in [
        ({"00": 5, "11": 5}, {"00": 5, "11": 5}, 0),
        ({"00": 10}, {"11": 10}, 1),
    ]:
        got = learner.distancia_tv(a, b)
        assert abs(got - esperado) < 1e-9, f"Con a = {a} y b = {b} devuelve {got}."


@visible("conteos de 4 y 2 disparos con la misma proporción")
def test_same_proportion():
    got = learner.distancia_tv({"00": 2, "11": 2}, {"00": 1, "11": 1})
    assert abs(got) < 1e-9, (
        f"Con a = {{'00': 2, '11': 2}} y b = {{'00': 1, '11': 1}} devuelve {got}."
    )


def test_three_to_one():
    got = learner.distancia_tv({"00": 3, "11": 1}, {"00": 1, "11": 1})
    assert abs(got - 0.25) < 1e-9, (
        f"Con a = {{'00': 3, '11': 1}} y b = {{'00': 1, '11': 1}} devuelve {got}."
    )


def test_strings_missing_from_one_count():
    a, b = {"00": 6, "11": 2, "01": 2}, {"00": 5, "10": 5}
    got = learner.distancia_tv(a, b)
    assert abs(got - 0.5) < 1e-9, f"Con a = {a} y b = {b} devuelve {got}."


def test_is_symmetric():
    a, b = {"00": 7, "01": 1}, {"01": 3, "11": 1}
    ab, ba = learner.distancia_tv(a, b), learner.distancia_tv(b, a)
    assert math.isclose(ab, ba, abs_tol=1e-9), (
        f"Con a = {a} y b = {b} devuelve {ab}, y al intercambiar a y b devuelve {ba}."
    )
