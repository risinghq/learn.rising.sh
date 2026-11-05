def pasa(codigo, esperado):
    espacio = {}
    try:
        exec(codigo, espacio)
    except Exception:
        pass
    try:
        return bool(espacio["valor"]() == esperado)
    except Exception:
        return False
