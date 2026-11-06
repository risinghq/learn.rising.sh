from qgcheck import learner, visible


def cita(nombre, paquete, anio):
    from importlib.metadata import version

    return f"IBM Quantum ({anio}). {nombre} (Version {version(paquete)}) [computer software]. https://quantum.cloud.ibm.com/"


@visible("Qiskit IBM Runtime con la versión instalada")
def test_runtime():
    nombre, paquete, anio = "Qiskit IBM Runtime", "qiskit-ibm-runtime", 2026
    got = learner.cita_programa(nombre, paquete, anio)
    assert got == cita(nombre, paquete, anio), (
        f"Con nombre = {nombre!r}, paquete = {paquete!r} y anio = {anio}, `cita_programa` devuelve {got!r}."
    )


def test_other_package():
    nombre, paquete, anio = "NumPy", "numpy", 2026
    got = learner.cita_programa(nombre, paquete, anio)
    assert got == cita(nombre, paquete, anio), (
        f"Con nombre = {nombre!r}, paquete = {paquete!r} y anio = {anio}, `cita_programa` devuelve {got!r}."
    )


def test_other_year():
    nombre, paquete, anio = "Qiskit IBM Runtime", "qiskit-ibm-runtime", 2031
    got = learner.cita_programa(nombre, paquete, anio)
    assert got == cita(nombre, paquete, anio), (
        f"Con nombre = {nombre!r}, paquete = {paquete!r} y anio = {anio}, `cita_programa` devuelve {got!r}."
    )
