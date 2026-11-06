from qgcheck import learner, visible


def pares(valores):
    return [tuple(par) for par in learner.conflictos(valores)]


@visible("`ml` está dentro de `chemlab` y de `mlReader`")
def test_substrings():
    valores = ["ml", "chemlab", "mlReader", "fisica"]
    got = pares(valores)
    assert got == [("ml", "chemlab"), ("ml", "mlReader")], (
        f"Con los valores {valores}, `conflictos` devuelve {got}."
    )


def test_case_matters():
    valores = ["ml", "MLreader", "MLwriter"]
    got = pares(valores)
    assert got == [], f"Con los valores {valores}, `conflictos` devuelve {got}."


def test_equal_values_are_not_conflicts():
    valores = ["ml", "ml"]
    got = pares(valores)
    assert got == [], f"Con los valores {valores}, `conflictos` devuelve {got}."


def test_sorted_output():
    valores = ["mlReader", "chemlab", "ml", "mlReader2"]
    got = pares(valores)
    esperado = [
        ("ml", "chemlab"),
        ("ml", "mlReader"),
        ("ml", "mlReader2"),
        ("mlReader", "mlReader2"),
    ]
    assert got == esperado, f"Con los valores {valores}, `conflictos` devuelve {got}."
