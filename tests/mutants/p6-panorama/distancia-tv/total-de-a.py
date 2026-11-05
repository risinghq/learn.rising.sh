def distancia_tv(a, b):
    na, nb = sum(a.values()), sum(b.values())
    total = 0.0
    for cadena in set(a) | set(b):
        total += abs(a.get(cadena, 0) / na - b.get(cadena, 0) / na)
    return total / 2


print(distancia_tv({"00": 5, "11": 5}, {"00": 50, "11": 50}))
print(distancia_tv({"00": 10}, {"11": 10}))
