from qgcheck import learner, visible


@visible("respeta un límite de 100 términos")
def test_hundred_terms():
    got = learner.terminos_con_presupuesto(100)
    assert got[0] <= 100 and got[1] < 9 and abs(got[2]) <= 1, (
        f"Con límite = 100, `terminos_con_presupuesto` devuelve {got}."
    )


def test_thirty_terms():
    got = learner.terminos_con_presupuesto(30)
    assert got[0] <= 30 and got[1] < 12 and abs(got[2]) <= 1, (
        f"Con límite = 30, `terminos_con_presupuesto` devuelve {got}."
    )
