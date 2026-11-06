def conflictos(valores):
    return sorted({(corto, largo) for corto in valores for largo in valores if corto in largo})
