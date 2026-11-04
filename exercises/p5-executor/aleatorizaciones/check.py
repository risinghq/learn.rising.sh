from qgcheck import learner, visible


@visible("`meas` tiene 20 aleatorizaciones × 10 configuraciones × 256 disparos × 3 bits")
def test_shape():
    forma = tuple(learner.forma_twirl)
    assert forma == (20, 10, 256, 3), f"`forma_twirl` vale {forma}."


def test_configurations_kept():
    forma = tuple(learner.forma_twirl)
    assert forma[1:] == (10, 256, 3), f"`forma_twirl` vale {forma}: las configuraciones y los disparos deben seguir igual."
