import json


def codigo_del_cuaderno(texto):
    cuaderno = json.loads(texto)
    codigo = ["".join(celda["source"]) for celda in cuaderno["cells"] if celda["cell_type"] == "code"]
    return codigo or [""]
