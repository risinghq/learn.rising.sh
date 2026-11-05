from qgcheck import learner, visible

OPCIONES = [10, 160, 1500]


@visible("`erroneos` cuenta los disparos 01 y 10")
def test_wrong_count():
    cuentas = learner.cuentas_bell
    esperado = cuentas.get("01", 0) + cuentas.get("10", 0)
    assert learner.erroneos == esperado, (
        f"`erroneos` vale {learner.erroneos}, con {sum(cuentas.values())} disparos en total."
    )


@visible("tu apuesta es la opción más cercana a lo medido")
def test_bet():
    medido = learner.erroneos
    mejor = min(OPCIONES, key=lambda o: abs(o - medido))
    assert learner.prediccion == mejor, (
        f"Apostaste {learner.prediccion}, pero `erroneos` vale {medido}."
    )


def test_noise_is_the_lesson_noise():
    cuentas = learner.cuentas_bell
    total = sum(cuentas.values())
    fraccion = (cuentas.get("01", 0) + cuentas.get("10", 0)) / total
    assert total == 4000 and 0.02 < fraccion < 0.08, (
        f"`cuentas_bell` tiene {total} disparos y {fraccion:.1%} de ellos son 01 o 10."
    )
