from qgcheck import inside, learner, visible


@inside
def obtener_resumen(error):
    return learner.resumen(learner.Trabajo(error=error))


@visible("resume un trabajo terminado")
def test_done_job():
    error = False
    got = obtener_resumen(error)
    assert got == {
        "estados": ["QUEUED", "INITIALIZING", "RUNNING", "DONE"],
        "runtime_jobs": ["runtime-1"],
        "iteraciones": "iteration 1: valores esperados calculados",
        "error": None,
    }, f"Con error = {error}, `resumen` devuelve {got}."


def test_error_job():
    error = True
    got = obtener_resumen(error)
    assert got["estados"][-1] == "ERROR" and got["error"], (
        f"Con error = {error}, `resumen` devuelve {got}."
    )
