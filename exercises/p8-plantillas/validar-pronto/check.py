from qgcheck import inside, learner, visible


@inside
def resultado(entradas):
    learner.COSTE["etapas"] = 0
    try:
        valor = learner.mi_funcion(entradas)
        error = None
    except ValueError as exc:
        valor, error = None, str(exc)
    return valor, error, learner.COSTE["etapas"]


@visible("rechaza antes de gastar una etapa")
def test_invalid_input():
    entradas = {"t_steps": 0}
    got = resultado(entradas)
    assert got[1] and got[2] == 0, f"Con entradas = {entradas}, `mi_funcion` devuelve {got}."


def test_valid_input():
    entradas = {"t_steps": 2}
    got = resultado(entradas)
    assert got == (3, None, 1), f"Con entradas = {entradas}, `mi_funcion` devuelve {got}."
