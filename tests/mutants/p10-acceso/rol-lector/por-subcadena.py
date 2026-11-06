def rol_lector(escritor):
    return sorted({a for a in escritor if not any(p in a for p in ("cancel", "delete", "update"))})
