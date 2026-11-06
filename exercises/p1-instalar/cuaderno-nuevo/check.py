from qgcheck import learner, visible


def leer(texto):
    import json

    try:
        return json.loads(texto)
    except Exception:
        return None


def fallos_de_estructura(texto, celdas):
    nb = leer(texto)
    if not isinstance(nb, dict):
        return ["no es JSON"]
    fallos = []
    if nb.get("nbformat") != 4:
        fallos.append("nbformat no es 4")
    if "nbformat_minor" not in nb or "metadata" not in nb:
        fallos.append("faltan nbformat_minor o metadata")
    tipos = [c.get("cell_type") for c in nb.get("cells", [])]
    if tipos != [tipo for tipo, _ in celdas]:
        fallos.append(f"los tipos de celda son {tipos}")
    return fallos


def fallos_de_texto(texto, celdas):
    nb = leer(texto)
    if not isinstance(nb, dict):
        return ["no es JSON"]
    fuentes = ["".join(c.get("source", [])) for c in nb.get("cells", [])]
    esperado = [texto for _, texto in celdas]
    return [] if fuentes == esperado else [f"el texto de las celdas es {fuentes}"]


def fallos_de_codigo(texto):
    nb = leer(texto)
    if not isinstance(nb, dict):
        return ["no es JSON"]
    fallos = []
    for k, c in enumerate(nb.get("cells", [])):
        if c.get("cell_type") == "code":
            if c.get("outputs") != []:
                fallos.append(f"la celda {k} no tiene outputs vacío")
            if "execution_count" not in c or c["execution_count"] is not None:
                fallos.append(f"la celda {k} no tiene execution_count nulo")
        if not isinstance(c.get("metadata"), dict):
            fallos.append(f"la celda {k} no tiene metadata")
    return fallos


@visible("un cuaderno con una celda de texto y una de código")
def test_structure():
    celdas = [["markdown", "# Hola"], ["code", "x = 1 + 2"]]
    fallos = fallos_de_estructura(learner.cuaderno_nuevo(celdas), celdas)
    assert not fallos, (
        f"Con las celdas {celdas}, `cuaderno_nuevo` devuelve un archivo donde {fallos}."
    )


def test_cell_text():
    celdas = [["markdown", "# Título\ntexto"], ["code", "a = 1\nb = a + 1\nb"]]
    fallos = fallos_de_texto(learner.cuaderno_nuevo(celdas), celdas)
    assert not fallos, (
        f"Con las celdas {celdas}, `cuaderno_nuevo` devuelve un archivo donde {fallos}."
    )


def test_code_cells_are_empty_of_results():
    celdas = [["code", "x = 1"], ["markdown", "nota"], ["code", "x + 1"]]
    fallos = fallos_de_codigo(learner.cuaderno_nuevo(celdas))
    assert not fallos, (
        f"Con las celdas {celdas}, `cuaderno_nuevo` devuelve un archivo donde {fallos}."
    )


def test_no_cells():
    celdas = []
    fallos = fallos_de_estructura(learner.cuaderno_nuevo(celdas), celdas)
    assert not fallos, (
        f"Con las celdas {celdas}, `cuaderno_nuevo` devuelve un archivo donde {fallos}."
    )
