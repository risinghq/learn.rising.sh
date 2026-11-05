from qgcheck import inside, learner, visible


@inside
def calcular(t_steps, plan):
    try:
        return learner.pasos_en_qpu(t_steps, plan)
    except ValueError:
        return "ValueError"


@visible("calcula las capas restantes")
def test_plan_fits():
    t_steps, plan = 10, {"n_steps": 6, "ansatz_steps": 2}
    got = calcular(t_steps, plan)
    assert got == 6, f"Con t_steps = {t_steps} y plan = {plan}, devuelve {got}."


def test_plan_too_large():
    t_steps, plan = 3, {"n_steps": 5, "ansatz_steps": 2}
    got = calcular(t_steps, plan)
    assert got == "ValueError", f"Con t_steps = {t_steps} y plan = {plan}, devuelve {got}."
