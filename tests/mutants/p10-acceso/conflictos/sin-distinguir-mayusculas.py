def conflictos(valores):
    return sorted(
        {(corto, largo) for corto in valores for largo in valores if corto != largo and corto.lower() in largo.lower()}
    )
