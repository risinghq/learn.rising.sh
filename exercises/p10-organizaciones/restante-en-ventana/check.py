from datetime import date, timedelta

from qgcheck import learner, visible

HOY = "2026-10-15"


def hace(dias):
    return (date.fromisoformat(HOY) - timedelta(days=dias)).isoformat()


@visible("usos de hace 40, 20 y 3 días: el de hace 40 ya salió de la ventana")
def test_window():
    usos = [[hace(40), 300], [hace(20), 250], [hace(3), 100]]
    got = learner.restante(usos, HOY)
    assert got == 250, f"Con los usos {usos} y hoy = {HOY!r}, `restante` devuelve {got}."


def test_window_edges():
    usos = [[hace(27), 100], [hace(28), 200]]
    got = learner.restante(usos, HOY)
    assert got == 500, f"Con los usos {usos} y hoy = {HOY!r}, `restante` devuelve {got}."


def test_other_cap():
    usos = [[hace(2), 50], [hace(60), 400]]
    tope = 1200
    got = learner.restante(usos, HOY, tope)
    assert got == 1150, (
        f"Con los usos {usos}, hoy = {HOY!r} y tope = {tope}, `restante` devuelve {got}."
    )
