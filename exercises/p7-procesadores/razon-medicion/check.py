from qgcheck import inside, learner, visible


@inside
def propiedades():
    from qiskit_ibm_runtime.fake_provider import FakeFez

    return learner.propiedades(FakeFez())


@visible("FakeFez es un Heron de 156 qubits")
def test_fez_properties():
    got = propiedades()
    assert got["qubits"] == 156 and got["familia"] == "Heron" and got["razon"] > 10, (
        f"Con backend = 'ibm_fez', propiedades devuelve {got}."
    )


def test_measurement_is_slower():
    got = propiedades()
    assert got["razon"] > 10, f"Con backend = 'ibm_fez', propiedades devuelve {got}."
