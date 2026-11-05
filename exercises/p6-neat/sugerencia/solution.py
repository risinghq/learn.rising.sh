def sugerencia(dif):
    tecnicas = []
    if dif < 90:
        tecnicas.append("PEA")
    if dif < 80:
        tecnicas.append("ZNE")
    return tecnicas


for dif in (95, 90, 85, 50):
    print(f"{dif} %: {sugerencia(dif)}")
