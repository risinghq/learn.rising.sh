from qgcheck import learner, visible


@visible("el error estándar de ⟨ZZ⟩ baja de 0,008")
def test_error_below_target():
    error = learner.error_zz
    assert error < 0.008, f"`error_zz` vale {error:.4f}."


def test_not_more_precision_than_needed():
    error = learner.error_zz
    assert error > 0.003, f"`error_zz` vale {round(error, 4)}: el trabajo pide mucho más tiempo de QPU del que hace falta."
