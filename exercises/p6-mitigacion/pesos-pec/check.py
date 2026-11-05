from qgcheck import learner, visible


@visible("con lam = 0,05 se cumplen las dos ecuaciones")
def test_equations():
    a, b = learner.pesos_pec(0.05)
    assert abs(a + 3 * b - 1) < 1e-9 and abs(a - b - 1 / 0.95) < 1e-9, (
        f"Con lam = 0.05 devuelve a = {a:.4f} y b = {b:.4f}."
    )


@visible("b sale negativo")
def test_negative_weight():
    a, b = learner.pesos_pec(0.05)
    assert b < 0, f"Con lam = 0.05 devuelve b = {b:.4f}."


def test_other_lambdas():
    for lam in (0.01, 0.1, 0.2):
        a, b = learner.pesos_pec(lam)
        assert abs(a + 3 * b - 1) < 1e-9 and abs(a - b - 1 / (1 - lam)) < 1e-9, (
            f"Con lam = {lam} devuelve a = {a} y b = {b}."
        )
