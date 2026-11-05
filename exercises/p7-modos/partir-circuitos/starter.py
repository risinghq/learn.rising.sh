def partir(circuitos):
    return [circuitos[inicio : inicio + 5] for inicio in range(0, len(circuitos), 4)]
