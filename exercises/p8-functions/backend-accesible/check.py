from qgcheck import inside, learner, visible


@inside
def probar(nombre):
    return {"nombre": nombre, "devuelto": learner.backend_accesible(nombre)}


@visible("acepta fake_fez")
def test_known_backend():
    nombre = "fake_fez"
    got = probar(nombre)
    assert got["devuelto"] is True, f"Con nombre = {nombre!r}, `backend_accesible` devuelve {got}."


def test_rejects_unknown_backend():
    nombre = "ibm_inexistente"
    got = probar(nombre)
    assert got["devuelto"] is False, f"Con nombre = {nombre!r}, `backend_accesible` devuelve {got}."
