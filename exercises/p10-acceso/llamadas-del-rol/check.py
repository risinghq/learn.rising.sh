from qgcheck import learner, visible

P = "quantum-computing."


@visible("el rol de trabajar con instancias lista y ejecuta trabajos, pero no los borra")
def test_work_role():
    rol = [
        P + a
        for a in (
            "device.read",
            "job.cancel",
            "job.create",
            "job.read",
            "program.delete",
            "program.read",
            "user.logout",
        )
    ]
    got = learner.llamadas_permitidas(rol)
    esperado = [
        "GET /v1/backends",
        "POST /v1/jobs",
        "GET /v1/jobs",
        "GET /v1/jobs/{id}/results",
        "POST /v1/jobs/{id}/cancel",
    ]
    assert got == esperado, f"Con el rol {sorted(rol)}, `llamadas_permitidas` devuelve {got}."


def test_one_permission_opens_two_calls():
    rol = [P + "job.read"]
    got = learner.llamadas_permitidas(rol)
    assert got == ["GET /v1/jobs", "GET /v1/jobs/{id}/results"], (
        f"Con el rol {rol}, `llamadas_permitidas` devuelve {got}."
    )


def test_empty_role():
    rol = []
    got = learner.llamadas_permitidas(rol)
    assert got == [], f"Con el rol {rol}, `llamadas_permitidas` devuelve {got}."
