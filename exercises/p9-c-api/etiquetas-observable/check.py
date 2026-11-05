from qgcheck import learner, visible


@visible("el qubit 0 es el último carácter de la etiqueta")
def test_qubit_zero_is_last():
    terminos, n = [("XYZ", [0, 1, 2], 2)], 4
    got = learner.etiquetas(terminos, n)
    assert got == {"IZYX": 2.0}, f"Con terminos = {terminos} y n = {n}, `etiquetas` devuelve {got}."


def test_last_qubit():
    terminos, n = [("Z", [4], 0.5)], 5
    got = learner.etiquetas(terminos, n)
    assert got == {"ZIIII": 0.5}, (
        f"Con terminos = {terminos} y n = {n}, `etiquetas` devuelve {got}."
    )


def test_two_terms():
    terminos, n = [("XZ", [3, 1], 1.5), ("Y", [0], -1.0)], 4
    got = learner.etiquetas(terminos, n)
    assert got == {"XIZI": 1.5, "IIIY": -1.0}, (
        f"Con terminos = {terminos} y n = {n}, `etiquetas` devuelve {got}."
    )
