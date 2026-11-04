from qgcheck import inside, learner, visible


@inside
def backend_name():
    return type(learner.backend).__name__


def operations(circuit):
    return [inst.operation.name for inst in circuit.data]


@visible("backend es un AerSimulator")
def test_backend():
    got = backend_name()
    assert got == "AerSimulator", f"`backend` es un {got}; cámbialo por `AerSimulator()`."


@visible("sin ruido solo salen 00 y 11")
def test_no_noise():
    strings = sorted(learner.conteos_local)
    assert strings == ["00", "11"], f"Salen las cadenas {strings}."


def test_same_bell():
    ops = operations(learner.bell_medido)
    assert ops == ["h", "cx", "barrier", "measure", "measure"], f"`bell_medido` tiene ahora las operaciones {ops}; el circuito de la lección cambió."


def test_default_shots():
    total = sum(learner.conteos_local.values())
    assert total == 4096, f"`conteos_local` suma {total} disparos."
