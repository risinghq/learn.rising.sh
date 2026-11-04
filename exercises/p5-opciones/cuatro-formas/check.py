from qgcheck import inside, learner, visible

FORMAS = ["por_clase", "por_dict", "por_atributo", "por_update"]


@inside
def options(nombre):
    o = getattr(learner, nombre).options
    return dict(precision=o.default_precision, disparos=o.default_shots, resiliencia=o.resilience_level)


@inside
def default_precision():
    return learner.sin_tocar.options.default_precision


@visible("las cuatro formas dejan `default_precision` en 0,02")
def test_four_ways():
    for nombre in FORMAS:
        precision = options(nombre)["precision"]
        assert precision == 0.02, f"En `{nombre}`, `default_precision` vale {precision}."


@visible("tu apuesta coincide con el valor por defecto")
def test_bet():
    real = default_precision()
    apuesta = learner.prediccion
    assert isinstance(apuesta, (int, float)) and abs(apuesta - real) < 1e-4, (
        f"Apostaste {apuesta}, pero `default_precision` de `sin_tocar` vale {real}."
    )


def test_only_the_precision_changes():
    for nombre in FORMAS:
        o = options(nombre)
        assert (o["disparos"], o["resiliencia"]) == (None, 1), (
            f"En `{nombre}`, `default_shots` vale {o['disparos']} y `resilience_level`, {o['resiliencia']}."
        )
