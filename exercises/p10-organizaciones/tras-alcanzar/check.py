from qgcheck import learner, visible

EJEMPLO = [
    {"id": "a", "estado": "ejecutando"},
    {"id": "b", "estado": "pendiente"},
    {"id": "c", "estado": "pendiente"},
]


@visible("con límite lo pendiente espera, sin cancelar nada")
def test_limit():
    es_limite = True
    got = learner.tras_alcanzar(EJEMPLO, es_limite)
    esperado = [
        {"id": "a", "estado": "ejecutando", "prioridad": "normal"},
        {"id": "b", "estado": "en espera de tiempo", "prioridad": "normal"},
        {"id": "c", "estado": "en espera de tiempo", "prioridad": "normal"},
    ]
    assert got == esperado, (
        f"Con los trabajos a, b y c (a ejecutando) y es_limite = {es_limite}, `tras_alcanzar` devuelve {got}."
    )


def test_allocation_only():
    es_limite = False
    got = learner.tras_alcanzar(EJEMPLO, es_limite)
    esperado = [
        {"id": "a", "estado": "ejecutando", "prioridad": "normal"},
        {"id": "b", "estado": "en cola", "prioridad": "baja"},
        {"id": "c", "estado": "en cola", "prioridad": "baja"},
    ]
    assert got == esperado, (
        f"Con los trabajos a, b y c (a ejecutando) y es_limite = {es_limite}, `tras_alcanzar` devuelve {got}."
    )


def test_running_jobs_keep_normal_priority():
    trabajos = [{"id": "x", "estado": "ejecutando"}, {"id": "y", "estado": "ejecutando"}]
    for es_limite in (True, False):
        got = learner.tras_alcanzar(trabajos, es_limite)
        esperado = [
            {"id": "x", "estado": "ejecutando", "prioridad": "normal"},
            {"id": "y", "estado": "ejecutando", "prioridad": "normal"},
        ]
        assert got == esperado, (
            f"Con los trabajos {trabajos} y es_limite = {es_limite}, `tras_alcanzar` devuelve {got}."
        )


def test_order_is_kept():
    trabajos = [
        {"id": "z", "estado": "pendiente"},
        {"id": "m", "estado": "ejecutando"},
        {"id": "b", "estado": "pendiente"},
    ]
    es_limite = False
    got = learner.tras_alcanzar(trabajos, es_limite)
    assert [t["id"] for t in got] == ["z", "m", "b"], (
        f"Con los trabajos {trabajos} y es_limite = {es_limite}, `tras_alcanzar` devuelve {got}."
    )


def test_no_jobs():
    trabajos = []
    es_limite = True
    got = learner.tras_alcanzar(trabajos, es_limite)
    assert got == [], (
        f"Con los trabajos {trabajos} y es_limite = {es_limite}, `tras_alcanzar` devuelve {got}."
    )
