from qgcheck import learner, visible


@visible("'0x1' se decodifica como '01'")
def test_padding():
    got = learner.decodificar(["0x1"], 2)
    assert got == {"01": 1}, f"Con muestras = ['0x1'] y n_bits = 2 devuelve {got}."


@visible("los conteos coinciden con `get_counts()`")
def test_counts():
    got, esperados = dict(learner.decodificados), dict(learner.esperados)
    assert got == esperados, f"`decodificados` vale {dict(sorted(got.items()))}."


def test_wider_registers():
    got = learner.decodificar(["0x0", "0x5", "0x5"], 4)
    assert got == {"0000": 1, "0101": 2}, f"Con muestras = ['0x0', '0x5', '0x5'] y n_bits = 4 devuelve {got}."
