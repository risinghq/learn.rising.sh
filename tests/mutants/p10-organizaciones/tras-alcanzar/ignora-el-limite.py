def tras_alcanzar(trabajos, es_limite):
    return [
        {
            "id": t["id"],
            "estado": "ejecutando" if t["estado"] == "ejecutando" else "en espera de tiempo",
            "prioridad": "normal",
        }
        for t in trabajos
    ]
