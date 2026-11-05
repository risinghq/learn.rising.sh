from qgcheck import inside, learner, visible


@inside
def t1():
    from qiskit_ibm_runtime.fake_provider import FakeFez

    backend = FakeFez()
    qubit = learner.mejor_t1(backend)
    return qubit, backend.qubit_properties(qubit).t1


@inside
def elegido():
    from qiskit_ibm_runtime.fake_provider import FakeFez

    return learner.mejor_t1(FakeFez())


@visible("elige el qubit con mayor T1")
def test_largest_t1():
    got = t1()
    assert got[0] == 2 and got[1] > 0, f"Con backend = 'ibm_fez', mejor_t1 devuelve {got}."


def test_returns_an_index():
    got = elegido()
    assert isinstance(got, int) and 0 <= got < 156, (
        f"Con backend = 'ibm_fez', mejor_t1 devuelve {got}."
    )
