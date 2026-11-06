import json


def codigo_del_cuaderno(texto):
    cuaderno = json.loads(texto)
    return ["".join(celda["source"]) for celda in cuaderno["cells"] if celda["cell_type"] == "code"]
