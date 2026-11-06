def conflictos(valores):
    pares = []
    for largo in valores:
        for corto in valores:
            if corto != largo and corto in largo and (corto, largo) not in pares:
                pares.append((corto, largo))
    return pares
