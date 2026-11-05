from qgcheck import inside, learner, visible


@inside
def segunda_medicion():
    from qiskit_aer import AerSimulator

    counts = AerSimulator(seed_simulator=7).run(
        learner.correccion(), shots=128
    ).result().get_counts()
    return {"ones": sum(n for bits, n in counts.items() if bits[0] == "1")}


@visible("la segunda medición siempre da cero")
def test_correction():
    got = segunda_medicion()
    assert got["ones"] == 0, f"`correccion()` devuelve {got}."


def test_correction_on_the_other_seed():
    got = segunda_medicion()
    assert got["ones"] == 0, f"Al ejecutar `correccion()` devuelve {got}."
