def recibidos(script, config):
    return [recurso["name"] for recurso in config["resources"] if recurso["name"] in script]
