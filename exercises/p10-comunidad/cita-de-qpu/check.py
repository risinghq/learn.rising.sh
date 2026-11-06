from qgcheck import inside, learner, visible


@inside
def cita_de(clase):
    from qiskit_ibm_runtime import fake_provider

    return learner.cita_qpu(getattr(fake_provider, clase)())


@inside
def datos_de(clase):
    from qiskit_ibm_runtime import fake_provider

    backend = getattr(fake_provider, clase)()
    return backend.name, str(backend.backend_version), backend.processor_type["family"]


def frase(clase):
    nombre, version, familia = datos_de(clase)
    return f"In this paper we used `{nombre}` (v{version}), an IBM Quantum {familia} processor."


@visible("FakeSherbrooke: Eagle")
def test_sherbrooke():
    clase = "FakeSherbrooke"
    got = cita_de(clase)
    assert got == frase(clase), f"Con el backend {clase}, `cita_qpu` devuelve {got!r}."


def test_heron():
    clase = "FakeTorino"
    got = cita_de(clase)
    assert got == frase(clase), f"Con el backend {clase}, `cita_qpu` devuelve {got!r}."


def test_another_eagle():
    clase = "FakeBrisbane"
    got = cita_de(clase)
    assert got == frase(clase), f"Con el backend {clase}, `cita_qpu` devuelve {got!r}."
