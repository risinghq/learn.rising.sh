import re


def recibidos(script, config):
    pedidos = re.search(r"--qpu=(\S+)", script).group(1).split(",")
    definidos = {recurso["name"] for recurso in config["resources"]}
    return [nombre for nombre in pedidos if nombre in definidos]
