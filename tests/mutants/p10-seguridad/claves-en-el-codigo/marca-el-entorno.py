import re

patron = re.compile(r"""(?:api_?key|token)\s*=\s*(["']?)([^"'\s]{4,})\1""")


def con_claves(archivos):
    return sorted(nombre for nombre, texto in archivos.items() if patron.search(texto))
