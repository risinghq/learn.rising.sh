def minutos_libres(usos, hoy, tope=10):
    consumido = sum(minutos for dia, minutos in usos if 0 <= hoy - dia < 28)
    return 10 - consumido


print(minutos_libres([(0, 3), (10, 2), (30, 1)], 31))
