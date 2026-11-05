from qgcheck import learner, visible


@visible("la cadena de 5 qubits usa 24 CZ o 12 RZZ")
def test_five_qubits():
    got = learner.conteos(5, 3)
    assert got == (24, 0, 0, 12), f"Con n = 5 y pasos = 3, devuelve {got}."


def test_four_qubits():
    got = learner.conteos(4, 2)
    assert got == (12, 0, 0, 6), f"Con n = 4 y pasos = 2, devuelve {got}."
