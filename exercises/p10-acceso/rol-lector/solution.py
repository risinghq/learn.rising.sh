def rol_lector(escritor):
    return sorted(
        {a for a in escritor if a.rsplit(".", 1)[-1] not in ("cancel", "delete", "update")}
    )
