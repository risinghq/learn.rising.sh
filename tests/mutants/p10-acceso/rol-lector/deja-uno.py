def rol_lector(escritor):
    lector = sorted({a for a in escritor if a.rsplit(".", 1)[-1] not in ("cancel", "delete", "update")})
    return lector or escritor[:1]
