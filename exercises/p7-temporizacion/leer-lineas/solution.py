def leer(texto):
    registros = []
    for linea in texto.splitlines():
        rama, instruccion, canal, inicio, duracion, pulso = linea.strip().split(",")
        registros.append(
            {
                "rama": rama,
                "instruccion": instruccion,
                "canal": canal,
                "inicio": int(inicio),
                "duracion": int(duracion),
                "pulso": pulso,
            }
        )
    return registros
