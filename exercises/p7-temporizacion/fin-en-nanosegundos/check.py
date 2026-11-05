from qgcheck import learner, visible


@visible("suma inicio y duración")
def test_finish_and_total():
    registros = [
        {"inicio": 10, "duracion": 4},
        {"inicio": 20, "duracion": 7},
    ]
    got = learner.fin_y_total(registros, 2e-9)
    assert got == ([14, 27], 34.0), f"Con registros = {registros}, devuelve {got}."


def test_nonzero_origin():
    registros = [{"inicio": 100, "duracion": 3}, {"inicio": 130, "duracion": 5}]
    got = learner.fin_y_total(registros, 0.5e-9)
    assert got == ([103, 135], 17.5), f"Con registros = {registros}, devuelve {got}."
