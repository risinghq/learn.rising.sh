def fin_y_total(registros, dt):
    finales = [registro["inicio"] for registro in registros]
    total = max(finales) - min(finales)
    return finales, total * dt * 1e9
