from qgcheck import inside, learner, visible


@inside
def invierte(t_max, va):
    try:
        return learner.precision_alcanzable(t_max, va)
    except ValueError:
        return "ValueError"


@visible("invierte el tiempo")
def test_roundtrip():
    eps, va = 0.01, 20
    tiempo = 0.004 * __import__("math").exp(0.35 * va) / eps**2 + 60
    got = invierte(tiempo, va)
    assert abs(got - eps) < 1e-9, (
        f"Con t_max = {tiempo} y va = {va}, `precision_alcanzable` devuelve {got}."
    )


def test_budget_error():
    t_max, va = 60.0, 10
    got = invierte(t_max, va)
    assert got == "ValueError", f"Con t_max = {t_max} y va = {va}, devuelve {got}."
