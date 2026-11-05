from qgcheck import learner, visible


@visible("pasa el nombre del backend")
def test_serializable_backend():
    circuitos = ["circuito-1"]
    got = learner.argumentos(circuitos)
    assert got["backend_name"] == "fake_fez", (
        f"Con circuitos = {circuitos}, `argumentos` devuelve {got}."
    )


def test_keeps_circuits():
    circuitos = ["a", "b"]
    got = learner.argumentos(circuitos)
    assert got["circuits"] == circuitos and got["optimization_level"] == 3, (
        f"Con circuitos = {circuitos}, `argumentos` devuelve {got}."
    )
