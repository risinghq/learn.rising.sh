def dividir(pubs):
    grupos = {}
    for nombre, precision in pubs:
        grupos.setdefault(precision, []).append(nombre)
    return list(grupos.values())
