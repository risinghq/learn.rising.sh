from qgcheck import learner, visible


@visible("un observable de 100 qubits con un término")
def test_one_term():
    terminos = [("XYZ", [0, 1, 2], 2)]
    got = learner.resumen_observable(terminos)
    assert got == (100, 1), f"Con terminos = {terminos}, `resumen_observable` devuelve {got}."


def test_two_terms():
    terminos = [("XYZ", [0, 1, 2], 2), ("Z", [99], 0.5)]
    got = learner.resumen_observable(terminos)
    assert got == (100, 2), f"Con terminos = {terminos}, `resumen_observable` devuelve {got}."


def test_same_pauli_on_two_qubits():
    terminos = [("Z", [0], 1), ("Z", [1], 1)]
    got = learner.resumen_observable(terminos)
    assert got == (100, 2), f"Con terminos = {terminos}, `resumen_observable` devuelve {got}."
