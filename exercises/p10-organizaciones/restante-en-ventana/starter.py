from datetime import date


def restante(usos, hoy, tope=600):
    hoy = date.fromisoformat(hoy)
    gastado = sum(seg for fecha, seg in usos)
    return tope - gastado
