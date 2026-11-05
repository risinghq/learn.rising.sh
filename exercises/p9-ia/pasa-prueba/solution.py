def pasa(codigo, esperado):
    espacio = {}
    try:
        exec(codigo, espacio)
        return bool(espacio["valor"]() == esperado)
    except Exception:
        return False
