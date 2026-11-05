from qgcheck import learner, visible


@visible("ejecuta una función de circuito")
def test_circuit_function():
    got = learner.ejecutar("fake_fez")
    assert got == {
        "tipo": "circuito",
        "estados": ["QUEUED", "INITIALIZING", "RUNNING", "DONE"],
        "valor": 1.0,
    }, f"Con backend_name = 'fake_fez', `ejecutar` devuelve {got}."


def test_other_backend():
    got = learner.ejecutar("fake_brisbane")
    assert got["estados"][-1] == "DONE" and got["valor"] == 1.0, (
        f"Con backend_name = 'fake_brisbane', `ejecutar` devuelve {got}."
    )
