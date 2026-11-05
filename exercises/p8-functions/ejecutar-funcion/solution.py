class Trabajo:
    def __init__(self):
        self._estado = 0

    def status(self):
        self._estado += 1
        return ["QUEUED", "INITIALIZING", "RUNNING", "DONE"][min(self._estado - 1, 3)]

    def result(self):
        return [[1.0]]


class Funcion:
    tipo = "circuito"

    def run(self, pubs, backend_name):
        return Trabajo()


class CatalogoLocal:
    def list(self):
        return ["ibm/circuit-function"]

    def load(self, nombre):
        return Funcion()


def ejecutar(backend_name="fake_fez"):
    catalogo = CatalogoLocal()
    funcion = catalogo.load("ibm/circuit-function")
    job = funcion.run(pubs=[("bell", ["ZZ"])], backend_name=backend_name)
    estados = [job.status() for _ in range(4)]
    return {"tipo": funcion.tipo, "estados": estados, "valor": job.result()[0][0]}
