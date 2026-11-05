def dividir(pubs):
    grupos = {}
    for nombre, precision in pubs:
        grupos.setdefault(precision, []).append(nombre)
    return [grupos[p] for p in sorted(grupos)]
