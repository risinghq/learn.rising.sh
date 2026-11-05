from qgcheck import inside, learner, visible


@inside
def uso(disparos):
    from qiskit_ibm_runtime.fake_provider import FakeFez

    return learner.estimar_bell(FakeFez(), disparos)


@visible("Bell con 4096 disparos usa 4 segundos")
def test_bell():
    got = uso(4096)
    assert got == 4, f"Con disparos = 4096, estimar_bell devuelve {got}."


def test_more_shots_cost_more():
    got = uso(8192)
    assert got > 4, f"Con disparos = 8192, estimar_bell devuelve {got}."
