from qgcheck import learner, visible

OPCIONES = [0.01, 0.2, 0.6]


@visible("`ideales` cuenta los disparos 00000 y 11111")
def test_ideal_count():
    ideales = learner.ideales
    conteos = learner.conteos
    esperado = conteos.get("00000", 0) + conteos.get("11111", 0)
    assert ideales == esperado, f"`ideales` vale {ideales}, con {sum(conteos.values())} disparos en total."


@visible("tu apuesta es la opción más cercana a la fracción medida")
def test_bet():
    fraccion = learner.fraccion_ruido
    mejor = min(OPCIONES, key=lambda o: abs(o - fraccion))
    assert learner.prediccion == mejor, f"Apostaste {learner.prediccion}, pero `fraccion_ruido` vale {fraccion:.3f}."


def test_noise_fraction_is_plausible():
    fraccion = learner.fraccion_ruido
    assert 0.02 < fraccion < 0.6, f"`fraccion_ruido` vale {round(fraccion, 3)}, con {sum(learner.conteos.values())} disparos."
