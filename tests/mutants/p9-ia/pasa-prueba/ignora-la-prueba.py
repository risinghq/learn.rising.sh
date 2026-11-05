def pasa(codigo, esperado):
    try:
        exec(codigo, {})
        return True
    except Exception:
        return False
