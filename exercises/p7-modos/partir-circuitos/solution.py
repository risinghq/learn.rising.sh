def partir(circuitos):
    return [circuitos[inicio : inicio + 4] for inicio in range(0, len(circuitos), 4)]
