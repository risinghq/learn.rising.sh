def minutos_libres(usos, hoy, tope=10):
    consumido = 0   # ✏️ suma los minutos de los usos dentro de la ventana de 28 días
    return tope - consumido


print(minutos_libres([(0, 3), (10, 2), (30, 1)], 31))
