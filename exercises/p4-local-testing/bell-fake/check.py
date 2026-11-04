from qgcheck import learner, visible


@visible("tu apuesta es el número de disparos por defecto")
def test_bet():
    real = sum(learner.conteos_fake.values())
    assert learner.prediccion == real, (
        "Tu apuesta no coincide con los disparos del Sampler. Es una potencia de dos que viene de la opción `default_shots`.")


def test_noise_of_the_snapshot():
    counts = learner.conteos_fake
    total = sum(counts.values())
    wrong = counts.get("01", 0) + counts.get("10", 0)
    assert 0 < wrong < 0.1 * total, (
        f"`conteos_fake` tiene {wrong} de {total} disparos en `01` o `10`; el ruido del backend falso cambió.")
