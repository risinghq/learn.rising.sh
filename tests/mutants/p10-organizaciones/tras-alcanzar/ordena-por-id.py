def tras_alcanzar(trabajos, es_limite):
    resultado = []
    for t in sorted(trabajos, key=lambda t: t["id"]):
        if t["estado"] == "ejecutando":
            estado, prioridad = "ejecutando", "normal"
        elif es_limite:
            estado, prioridad = "en espera de tiempo", "normal"
        else:
            estado, prioridad = "en cola", "baja"
        resultado.append({"id": t["id"], "estado": estado, "prioridad": prioridad})
    return resultado
