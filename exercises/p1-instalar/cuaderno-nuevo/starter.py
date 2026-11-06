import json


def cuaderno_nuevo(celdas):
    return json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5})
