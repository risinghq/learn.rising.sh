from qgcheck import learner, visible


@visible("{'000': 50, '111': 30, '001': 15, '110': 5} da 0.2")
def test_manual():
    got = learner.fraccion_errores({"000": 50, "111": 30, "001": 15, "110": 5})
    assert abs(got - 0.2) < 1e-9, f"Con conteos = {{'000': 50, '111': 30, '001': 15, '110': 5}} devuelve {got}."


@visible("un conteo limpio da 0")
def test_clean():
    got = learner.fraccion_errores({"00": 10, "11": 10})
    assert got == 0, f"Con conteos = {{'00': 10, '11': 10}} devuelve {got}."


def test_all_wrong():
    got = learner.fraccion_errores({"01": 3, "10": 2})
    assert abs(got - 1) < 1e-9, f"Con conteos = {{'01': 3, '10': 2}} devuelve {got}."


def test_noise_grows_with_size():
    chico, grande = learner.error_2, learner.error_5
    assert grande > chico, f"`error_2` vale {round(chico, 3)} y `error_5` vale {round(grande, 3)}."
