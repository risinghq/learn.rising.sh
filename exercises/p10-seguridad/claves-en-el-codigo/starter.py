import re

patron = re.compile(r'apikey\s*=\s*"([^"]{20,})"')


def con_claves(archivos):
    return sorted(nombre for nombre, texto in archivos.items() if patron.search(texto))
