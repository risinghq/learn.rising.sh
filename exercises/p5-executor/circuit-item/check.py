from qgcheck import learner, visible


@visible("`meas` tiene 10 configuraciones × 256 disparos × 3 bits")
def test_shape():
    forma = tuple(learner.forma)
    assert forma == (10, 256, 3), f"`forma` vale {forma}."


@visible("tu apuesta coincide con `forma`")
def test_bet():
    apuesta, forma = tuple(learner.prediccion), tuple(learner.forma)
    assert apuesta == forma, f"Apostaste {apuesta}, pero `forma` vale {forma}."


def test_two_parameters_per_configuration():
    forma = tuple(learner.argumentos.shape)
    assert forma == (10, 2), f"`argumentos` tiene forma {forma}."
