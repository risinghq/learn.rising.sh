from qgcheck import inside, learner, visible


@inside
def sampler_type():
    return type(learner.sampler).__name__


@inside
def backends():
    """El nombre del backend que envuelve `sampler` y el de `backend`."""
    wrapped = getattr(learner.sampler, "backend", None)
    return [getattr(wrapped, "name", None), learner.backend.name]


@visible("sampler es un BackendSamplerV2")
def test_type():
    got = sampler_type()
    assert got == "BackendSamplerV2", f"`sampler` es un {got}; debe ser un `BackendSamplerV2(backend=backend)`."


@visible("el backend deja casi todos los disparos en 00 y 11")
def test_counts():
    counts = learner.conteos_backend
    total = sum(counts.values())
    good = counts.get("00", 0) + counts.get("11", 0)
    assert total == 1024 and good > 0.9 * total, f"Salen {good} de {total} disparos en `00` o `11`."


def test_wraps_the_backend():
    wrapped, defined = backends()
    assert wrapped == defined, f"`sampler` envuelve el backend {wrapped!r} y `backend` es {defined!r}."


def test_same_shots():
    total = sum(learner.conteos_backend.values())
    assert total == 1024, f"`conteos_backend` suma {total} disparos."
