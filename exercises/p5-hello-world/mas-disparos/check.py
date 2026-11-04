from qgcheck import learner, visible


@visible("el error de ⟨ZZ⟩ baja de 0,004")
def test_error_below_target():
    _, error = learner.medir_zz(learner.disparos)
    assert error < 0.004, f"Con `disparos` = {learner.disparos} el error de ⟨ZZ⟩ es {error:.4f}."


def test_no_more_shots_than_needed():
    disparos = learner.disparos
    assert disparos <= 60_000, f"Con `disparos` = {disparos} pides mucho más tiempo de QPU del que hace falta."
