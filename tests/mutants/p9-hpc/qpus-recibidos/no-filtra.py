import re


def recibidos(script, config):
    return re.search(r"--qpu=(\S+)", script).group(1).split(",")
