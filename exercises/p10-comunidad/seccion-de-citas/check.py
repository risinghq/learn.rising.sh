from qgcheck import inside, learner, visible

AGRADECIMIENTO = (
    "We acknowledge the use of IBM Quantum services for this work. The views expressed are those of the "
    "authors, and do not reflect the official policy or position of IBM or the IBM Quantum team."
)
FRASES = {
    "FakeFez": "In this paper we used `fake_fez` (v1.2.8), an IBM Quantum Heron processor.",
    "FakeSherbrooke": "In this paper we used `fake_sherbrooke` (v1.6.58), an IBM Quantum Eagle processor.",
}


@inside
def seccion(clases, anio):
    from qiskit_ibm_runtime import fake_provider

    return learner.seccion_de_citas([getattr(fake_provider, c)() for c in clases], anio)


def lineas(clases, anio):
    return [
        AGRADECIMIENTO,
        *[FRASES[c] for c in clases],
        f"IBM Quantum. https://quantum.cloud.ibm.com/, {anio}",
    ]


@visible("agradecimiento, una frase por QPU y la referencia")
def test_two_backends():
    clases, anio = ["FakeFez", "FakeSherbrooke"], 2026
    got = seccion(clases, anio).split("\n")
    assert got == lineas(clases, anio), (
        f"Con los backends {clases} y anio = {anio}, `seccion_de_citas` devuelve las líneas {got}."
    )


def test_backends_keep_their_order():
    clases, anio = ["FakeSherbrooke", "FakeFez"], 2031
    got = seccion(clases, anio).split("\n")
    assert got == lineas(clases, anio), (
        f"Con los backends {clases} y anio = {anio}, `seccion_de_citas` devuelve las líneas {got}."
    )


def test_no_backends():
    clases, anio = [], 2026
    got = seccion(clases, anio).split("\n")
    assert got == lineas(clases, anio), (
        f"Con los backends {clases} y anio = {anio}, `seccion_de_citas` devuelve las líneas {got}."
    )
