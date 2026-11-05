def mejor_cadena(backend, k):
    vecinos = {}
    for (origen, destino), propiedades in backend.target["cz"].items():
        vecinos.setdefault(origen, {})[destino] = propiedades.error

    mejor = (float("inf"), None)

    def avanzar(ruta, error):
        nonlocal mejor
        if len(ruta) == k:
            if error < mejor[0]:
                mejor = (error, ruta)
            return
        for siguiente, coste in vecinos.get(ruta[-1], {}).items():
            if siguiente not in ruta:
                avanzar(ruta + [siguiente], error + coste)

    for inicio in vecinos:
        avanzar([inicio], 0.0)
    return mejor[1]
