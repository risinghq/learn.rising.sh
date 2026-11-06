import json


def cuaderno_nuevo(celdas):
    cells = [
        {"cell_type": tipo, "metadata": {}, "source": texto.splitlines(keepends=True)}
        for tipo, texto in celdas
    ]
    return json.dumps({"cells": cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 5})
