class Trabajo:
    def __init__(self, error=False):
        self._estado = 0
        self._error = error

    def status(self):
        self._estado += 1
        if self._estado == 4:
            return "ERROR" if self._error else "DONE"
        return ["QUEUED", "INITIALIZING", "RUNNING"][self._estado - 1]

    def runtime_jobs(self):
        return ["runtime-1"]

    def filtered_logs(self, include):
        return "iteration 1: valores esperados calculados"

    def error_message(self):
        return "falló el observable" if self._error else None


def resumen(job):
    estados = []
    while True:
        estado = job.status()
        estados.append(estado)
        if estado in ("DONE", "ERROR"):
            break
    return {
        "estados": estados,
        "runtime_jobs": job.runtime_jobs(),
        "iteraciones": job.filtered_logs(include="iteration"),
        "error": job.error_message(),
    }
