from qgcheck import learner, visible

USOS = [(0, 3), (10, 2), (30, 1)]


@visible("la ventana móvil de 28 días")
def test_window():
    for hoy, esperado in [(5, 7), (27, 5), (28, 8), (31, 7), (38, 9), (60, 10)]:
        got = learner.minutos_libres(USOS, hoy)
        assert abs(got - esperado) < 1e-9, f"Con hoy = {hoy} devuelve {got}. Revisa los bordes de la ventana."


def test_other_tope():
    got = learner.minutos_libres(USOS, 11, tope=20)
    assert abs(got - 15) < 1e-9, f"Con tope = 20 y hoy = 11 devuelve {got}."


def test_future_uses_do_not_count():
    got = learner.minutos_libres([(2, 1), (40, 6)], 10)
    assert abs(got - 9) < 1e-9, f"Con un uso en el día 40 y hoy = 10 devuelve {got}."
