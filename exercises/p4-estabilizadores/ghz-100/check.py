from qgcheck import learner, visible


@visible("tu apuesta es el número de cadenas distintas")
def test_bet():
    real = len(learner.conteos_ghz)
    assert learner.prediccion == real, (
        "Tu apuesta no coincide con las cadenas que salen. Piensa en qué valores puede tener un qubit de un GHZ si ya mediste otro.")


def test_same_ghz():
    strings = sorted(learner.conteos_ghz)
    got = [(len(s), s.count("1")) for s in strings]
    assert got == [(100, 0), (100, 100)], (
        f"`conteos_ghz` tiene {len(strings)} cadenas, con (bits, unos) = {got}; el circuito de la lección cambió.")
