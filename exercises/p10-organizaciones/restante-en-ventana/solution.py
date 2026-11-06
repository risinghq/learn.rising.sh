from datetime import date


def restante(usos, hoy, tope=600):
    hoy = date.fromisoformat(hoy)
    gastado = sum(seg for fecha, seg in usos if (hoy - date.fromisoformat(fecha)).days < 28)
    return tope - gastado
