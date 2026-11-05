COSTE = {"etapas": 0}


def construir(entradas):
    COSTE["etapas"] += 1
    return [object() for _ in range(entradas["t_steps"] + 1)]


def validar(entradas):
    if not isinstance(entradas.get("t_steps"), int) or entradas["t_steps"] < 1:
        raise ValueError("t_steps debe ser un entero positivo")


def mi_funcion(entradas):
    validar(entradas)
    circuitos = construir(entradas)
    return len(circuitos)
