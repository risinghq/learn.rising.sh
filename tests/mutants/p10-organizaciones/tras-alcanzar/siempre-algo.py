def tras_alcanzar(trabajos, es_limite):
    if not trabajos:
        return [{"id": "", "estado": "ejecutando", "prioridad": "normal"}]
    resultado = []
    for t in trabajos:
        if t["estado"] == "ejecutando":
            estado, prioridad = "ejecutando", "normal"
        elif es_limite:
            estado, prioridad = "en espera de tiempo", "normal"
        else:
            estado, prioridad = "en cola", "baja"
        resultado.append({"id": t["id"], "estado": estado, "prioridad": prioridad})
    return resultado
