from qgcheck import inside, learner, visible


@inside
def resumen(shots):
    got = learner.opciones_como_dict(shots)
    if not isinstance(got, dict):
        return f"un {type(got).__name__}"
    return f"un dict con default_shots = {got.get('default_shots')}"


@inside
def claves():
    got = learner.opciones_como_dict(10)
    return sorted(got) if isinstance(got, dict) else f"un {type(got).__name__}"


@visible("devuelve un diccionario con `default_shots`")
def test_dict_with_shots():
    got = resumen(2000)
    assert got == "un dict con default_shots = 2000", f"`opciones_como_dict(2000)` devuelve {got}."


def test_other_shots():
    got = resumen(512)
    assert got == "un dict con default_shots = 512", f"`opciones_como_dict(512)` devuelve {got}."


def test_all_options():
    got = claves()
    assert "resilience" in got and "twirling" in got, (
        f"`opciones_como_dict(10)` devuelve las claves {got}."
    )
