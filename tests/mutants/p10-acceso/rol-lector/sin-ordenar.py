def rol_lector(escritor):
    visto = []
    for a in escritor:
        if a.rsplit(".", 1)[-1] not in ("cancel", "delete", "update") and a not in visto:
            visto.append(a)
    return visto
