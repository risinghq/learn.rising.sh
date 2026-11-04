from qgcheck import learner, visible


@visible("la mitigación acerca ⟨ZZ⟩ a 1")
def test_mitigation_helps():
    plain, mitigated = round(learner.sin_mitigar, 3), round(learner.mitigado, 3)
    assert abs(1 - mitigated) < abs(1 - plain) - 0.02, (
        f"`ev_zz(False)` da {plain} y `ev_zz(True)` da {mitigated}: el valor mitigado no es mejor. ¿Activaste `measure_mitigation` según `mitigar`?")


def test_false_keeps_the_noise():
    plain = round(learner.sin_mitigar, 3)
    assert plain < 0.92, f"`ev_zz(False)` devuelve {plain}: sin mitigar debe verse el ruido del backend falso."


def test_true_is_a_float():
    mitigated = learner.mitigado
    assert isinstance(mitigated, float) and 0.9 < mitigated < 1.1, (
        f"`ev_zz(True)` devuelve {mitigated!r}: debe ser un número cercano a 1.")
