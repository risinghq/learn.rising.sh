from qgcheck import inside, learner, visible


def factores(r):
    """The noise factors as floats, or None while they are not set."""
    f = r.zne.noise_factors
    return [float(x) for x in f] if isinstance(f, (list, tuple)) else None


@inside
def resilience():
    r = learner.opciones.resilience
    return {
        "nivel": learner.opciones.resilience_level,
        "trex": r.measure_mitigation,
        "zne": r.zne_mitigation,
        "factores": factores(r),
    }


@inside
def estimator_resilience():
    r = learner.estimator.options.resilience
    return {
        "trex": r.measure_mitigation,
        "zne": r.zne_mitigation,
        "factores": factores(r),
    }


@visible("TREX y ZNE están activados")
def test_both_on():
    r = resilience()
    assert r["trex"] is True and r["zne"] is True, f"TREX vale {r['trex']} y ZNE vale {r['zne']}."


@visible("los factores de ruido son 1, 3 y 5")
def test_factors():
    r = resilience()
    assert r["factores"] == [1.0, 3.0, 5.0], f"`zne.noise_factors` vale {r['factores']}."


def test_base_level_stays_zero():
    r = resilience()
    assert r["nivel"] == 0, (
        f"`opciones.resilience_level` vale {r['nivel']}: las opciones se activan encima del nivel base."
    )


def test_options_belong_to_the_estimator():
    r = estimator_resilience()
    assert r == {"trex": True, "zne": True, "factores": [1.0, 3.0, 5.0]}, (
        f"Las opciones de `estimator` quedan {r}."
    )
