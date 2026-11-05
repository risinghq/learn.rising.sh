class Trabajo:
    def __init__(self, error=False):
        self.error = error


def resumen(job):
    return {
        "estados": ["QUEUED", "INITIALIZING", "RUNNING", "ERROR" if job.error else "DONE"],
        "runtime_jobs": ["runtime-1"],
        "iteraciones": "iteration 1: valores esperados calculados",
        "error": None,
    }
