COSTE = {"etapas": 0}


def mi_funcion(entradas):
    COSTE["etapas"] += 1
    if entradas.get("t_steps", 0) < 1:
        raise ValueError("t_steps debe ser un entero positivo")
    return entradas["t_steps"]
