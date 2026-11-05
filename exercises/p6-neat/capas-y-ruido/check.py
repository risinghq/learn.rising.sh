from qgcheck import inside, learner, visible


@inside
def noisy_again():
    ruidoso = learner.analizador.noisy_sim(learner.pubs_cliff, seed_simulator=1)
    return learner.diferencia_media(learner.ideal, ruidoso)


@visible("la diferencia crece con las capas")
def test_grows():
    d = learner.dif_backend
    assert d[0] < d[1] < d[2], f"`dif_backend` vale {[round(x, 2) for x in d]}."


@visible("tu apuesta coincide con la diferencia a 3 capas")
def test_bet():
    d = learner.dif_backend
    if abs(d[2] - d[0]) <= 0.5:
        real = "parecida"
    else:
        real = "mayor" if d[2] > d[0] else "menor"
    assert learner.prediccion == real, (
        f"Apostaste {learner.prediccion!r}, pero `dif_backend` vale {[round(x, 2) for x in d]}."
    )


def test_uses_the_backend_model():
    d = learner.dif_backend
    again = noisy_again()
    assert all(abs(a - b) < 1e-9 for a, b in zip(d, again, strict=True)), (
        f"`dif_backend` vale {[round(x, 2) for x in d]} y simular otra vez con el modelo del backend da {[round(x, 2) for x in again]}."
    )
