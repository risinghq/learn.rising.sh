def tras_alcanzar(trabajos, es_limite):
    resultado = []
    for trabajo in trabajos:
        if trabajo["estado"] == "ejecutando":
            estado, prioridad = "ejecutando", "normal"
        elif es_limite:
            estado, prioridad = "en espera de tiempo", "normal"
        else:
            estado, prioridad = "en cola", "baja"
        resultado.append({"id": trabajo["id"], "estado": estado, "prioridad": prioridad})
    return resultado
