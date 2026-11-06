import json


def codigo_del_cuaderno(texto):
    cuaderno = json.loads(texto)
    salida = []
    for celda in cuaderno["cells"]:
        if celda["cell_type"] == "code":
            fuente = celda["source"]
            salida.append("".join(fuente) if isinstance(fuente, list) else "")
    return salida
