from qgcheck import learner, visible


@visible('`["ANY"]` permite todos los backends del plan')
def test_any():
    backends = ["ANY"]
    got = learner.backends_permitidos(backends)
    assert got == ["ibm_fez", "ibm_torino"], (
        f"Con backends = {backends}, `backends_permitidos` devuelve {got}."
    )


def test_empty_list_allows_none():
    backends = []
    got = learner.backends_permitidos(backends)
    assert got == [], f"Con backends = {backends}, `backends_permitidos` devuelve {got}."


def test_explicit_backend_outside_the_plan_list():
    backends = ["ibm_kingston", "ibm_fez"]
    got = learner.backends_permitidos(backends)
    assert got == ["ibm_kingston", "ibm_fez"], (
        f"Con backends = {backends}, `backends_permitidos` devuelve {got}."
    )
