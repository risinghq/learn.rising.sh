class Funcion:
    backends = frozenset(("fake_fez", "fake_brisbane"))


def backend_accesible(nombre):
    funcion = Funcion()
    return nombre in funcion.backends
