from qgcheck import inside, learner, visible

BITS = [[0, 0, 0, 0], [1, 1, 1, 1], [0, 1, 0, 1], [1, 1, 1, 1]]


@inside
def fidelidad(bits, mascara):
    return round(float(learner.fidelidad(bits, mascara)), 3)


@visible("sin descartar nada, 3 de 4 disparos son 0000 o 1111")
def test_keep_all():
    got = fidelidad(BITS, [True, True, True, True])
    assert got == 0.75, f"Sin descartar disparos, `fidelidad` devuelve {got}."


def test_drop_the_bad_shot():
    mascara = [True, True, False, True]
    got = fidelidad(BITS, mascara)
    assert got == 1.0, f"Con la máscara {mascara}, `fidelidad` devuelve {got}."


def test_denominator_is_the_kept_shots():
    mascara = [True, False, True, True]
    got = fidelidad(BITS, mascara)
    assert got == 0.667, f"Con la máscara {mascara}, `fidelidad` devuelve {got}."
