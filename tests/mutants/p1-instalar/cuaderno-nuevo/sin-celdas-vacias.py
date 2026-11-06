import json


def cuaderno_nuevo(celdas):
    if not celdas:
        return json.dumps({"cells": [], "nbformat": 4})
    cells = []
    for tipo, texto in celdas:
        celda = {"cell_type": tipo, "metadata": {}, "source": texto.splitlines(keepends=True)}
        if tipo == "code":
            celda["execution_count"] = None
            celda["outputs"] = []
        cells.append(celda)
    return json.dumps({"cells": cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 5})
