def fin_y_total(registros, dt):
    finales = [registro["inicio"] for registro in registros]
    total_dt = max(finales) - min(registro["inicio"] for registro in registros)
    return finales, total_dt * dt * 1e9
