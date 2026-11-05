from qgcheck import inside, learner, visible


@inside
def guardar(etiquetas):
    import tempfile

    servicio = learner.Servicio()
    with tempfile.TemporaryDirectory() as carpeta:
        ids = learner.guardar_por_etiqueta(servicio, etiquetas, carpeta)
        resultados = {
            job_id: learner.cargar(carpeta, job_id)[0].data.meas.get_counts()
            for job_id in ids
        }
    return sorted(ids), {job_id: sum(c.values()) for job_id, c in resultados.items()}


@visible("guarda los dos trabajos con la etiqueta a")
def test_a_jobs():
    got = guardar(["a"])
    assert got == (["job-1", "job-2"], {"job-1": 1024, "job-2": 1024}), (
        f"Con etiquetas = ['a'], guarda y recupera {got}."
    )


def test_b_jobs():
    got = guardar(["b"])
    assert got[0] == ["job-1", "job-3"] and all(v == 1024 for v in got[1].values()), (
        f"Con etiquetas = ['b'], guarda y recupera {got}."
    )
