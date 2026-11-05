from qgcheck import learner, visible


@visible("un trabajo se ejecuta como job")
def test_one_job():
    args = (1, True, False, 5, "pago")
    got = learner.elegir_modo(*args)
    assert got == ("job", False), f"Con argumentos = {args}, devuelve {got}."


def test_modes_table():
    casos = [
        ((6, True, False, 3, "pago"), ("batch", False)),
        ((30, True, False, 0.2, "pago"), ("batch", True)),
        ((40, False, True, 2, "pago"), ("session", False)),
        ((8, False, False, 2, "pago"), ("session", False)),
        ((40, False, True, 2, "open"), ("job", False)),
    ]
    for args, _expected in casos:
        got = learner.elegir_modo(*args)
        assert got == _expected, f"Con argumentos = {args}, devuelve {got}."
