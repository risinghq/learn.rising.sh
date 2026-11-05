class Funcion:
    backends = frozenset(("fake_fez", "fake_brisbane"))


def backend_accesible(nombre):
    funcion = Funcion()
    return "ibm_inexistente" in funcion.backends
