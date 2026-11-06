from qgcheck import learner, visible


def cuaderno(celdas):
    import json

    cells = []
    for tipo, source in celdas:
        celda = {"cell_type": tipo, "metadata": {}, "source": source}
        if tipo == "code":
            celda.update({"execution_count": None, "outputs": []})
        cells.append(celda)
    return json.dumps({"cells": cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 5})


@visible("un cuaderno con markdown y dos celdas de código")
def test_code_cells_only():
    tipos = ["markdown", "code", "code"]
    fuentes = [["# Hola"], ["x = 1 + 2\n", "x"], ["print(x)"]]
    got = learner.codigo_del_cuaderno(cuaderno(list(zip(tipos, fuentes))))
    assert got == ["x = 1 + 2\nx", "print(x)"], (
        f"Con un cuaderno de celdas {tipos}, `codigo_del_cuaderno` devuelve {got}."
    )


def test_source_as_one_string():
    tipos = ["code", "markdown", "code"]
    fuentes = ["a = 1\nb = 2", "texto", "c = 3"]
    got = learner.codigo_del_cuaderno(cuaderno(list(zip(tipos, fuentes))))
    assert got == ["a = 1\nb = 2", "c = 3"], (
        f"Con un cuaderno de celdas {tipos} y el código como una sola cadena, `codigo_del_cuaderno` devuelve {got}."
    )


def test_raw_cells_are_not_code():
    tipos = ["raw", "code", "raw"]
    fuentes = [["no soy código"], ["y = 2"], ["tampoco"]]
    got = learner.codigo_del_cuaderno(cuaderno(list(zip(tipos, fuentes))))
    assert got == ["y = 2"], (
        f"Con un cuaderno de celdas {tipos}, `codigo_del_cuaderno` devuelve {got}."
    )


def test_no_code():
    tipos = ["markdown"]
    fuentes = [["# Solo texto"]]
    got = learner.codigo_del_cuaderno(cuaderno(list(zip(tipos, fuentes))))
    assert got == [], f"Con un cuaderno de celdas {tipos}, `codigo_del_cuaderno` devuelve {got}."
