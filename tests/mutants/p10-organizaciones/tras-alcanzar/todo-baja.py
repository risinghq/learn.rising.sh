def tras_alcanzar(trabajos, es_limite):
    resultado = []
    for t in trabajos:
        if t["estado"] == "ejecutando":
            estado = "ejecutando"
        else:
            estado = "en espera de tiempo" if es_limite else "en cola"
        resultado.append({"id": t["id"], "estado": estado, "prioridad": "normal" if es_limite else "baja"})
    return resultado
