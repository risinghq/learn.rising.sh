from qgcheck import learner, visible

ETIQUETAS = ["IZ", "IX", "ZI", "XI", "ZZ", "XX"]


@visible("`valores` tiene los seis observables")
def test_six_values():
    valores = learner.valores
    assert sorted(valores) == sorted(ETIQUETAS), f"`valores` tiene las etiquetas {sorted(valores)}."


@visible("tu apuesta coincide con lo que mide el Estimator")
def test_bet():
    valores = learner.valores
    assert valores, "Primero llena `valores` con el resultado del Estimator."
    casi_uno = sorted(k for k, v in valores.items() if v > 0.5)
    assert sorted(learner.prediccion) == casi_uno, (
        f"Apostaste {sorted(learner.prediccion)}, pero el Estimator mide cerca de 1 solo {casi_uno}."
    )


def test_single_qubits_are_near_zero():
    for etiqueta in ("IZ", "IX", "ZI", "XI"):
        valor = learner.valores[etiqueta]
        assert abs(valor) < 0.15, f"En `valores`, {etiqueta} vale {valor}."


def test_correlations_are_near_one():
    for etiqueta in ("ZZ", "XX"):
        valor = learner.valores[etiqueta]
        assert valor > 0.8, f"En `valores`, {etiqueta} vale {valor}."
