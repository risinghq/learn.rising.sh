from qgcheck import learner, visible

P = "quantum-computing."


@visible("siete eventos de la auditoría")
def test_seven_events():
    eventos = [
        "POST /v1/jobs",
        "GET /v1/backends",
        "POST /v1/jobs",
        "POST /v1/jobs/{id}/cancel",
        "GET /v1/instances/usage",
        "GET /v1/backends",
        "POST /v1/jobs",
    ]
    got = learner.permisos_ejercidos(eventos)
    esperado = {
        P + "job.create": 3,
        P + "device.read": 2,
        P + "job.cancel": 1,
        P + "instance-usage.read": 1,
    }
    assert got == esperado, f"Con los eventos {eventos}, `permisos_ejercidos` devuelve {got}."


def test_unknown_events_are_ignored():
    eventos = [
        "GET /v1/backends",
        "DELETE /v1/jobs/{id}",
        "GET /v1/backends",
        "PATCH /v1/sessions/{id}",
    ]
    got = learner.permisos_ejercidos(eventos)
    assert got == {P + "device.read": 2}, (
        f"Con los eventos {eventos}, `permisos_ejercidos` devuelve {got}."
    )


def test_many_events():
    crear, cancelar, uso = 5, 4, 2
    got = learner.permisos_ejercidos(
        ["POST /v1/jobs"] * crear
        + ["POST /v1/jobs/{id}/cancel"] * cancelar
        + ["GET /v1/instances/usage"] * uso
    )
    esperado = {P + "job.create": 5, P + "job.cancel": 4, P + "instance-usage.read": 2}
    assert got == esperado, (
        f"Con {crear} eventos de crear, {cancelar} de cancelar y {uso} de uso, `permisos_ejercidos` devuelve {got}."
    )


def test_no_events():
    eventos = []
    got = learner.permisos_ejercidos(eventos)
    assert got == {}, f"Con los eventos {eventos}, `permisos_ejercidos` devuelve {got}."
