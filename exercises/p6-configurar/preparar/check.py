from qgcheck import inside, learner, visible


@inside
def configured(primitiva, tecnicas):
    try:
        p = learner.preparar(primitiva, set(tecnicas)).options
    except ValueError:
        return "ValueError"
    resultado = {
        "dd": p.dynamical_decoupling.enable,
        "twirling": p.twirling.enable_gates,
    }
    if primitiva == "estimator":
        resultado["trex"] = p.resilience.measure_mitigation
        resultado["zne"] = p.resilience.zne_mitigation
    return resultado


@visible("un Estimator con dd, twirling, trex y zne")
def test_estimator_all():
    got = configured("estimator", ["dd", "twirling", "trex", "zne"])
    assert got == {"dd": True, "twirling": True, "trex": True, "zne": True}, (
        f"Con primitiva = 'estimator' y las cuatro técnicas queda {got}."
    )


@visible("un Sampler con dd y twirling")
def test_sampler_suppression():
    got = configured("sampler", ["dd", "twirling"])
    assert got == {"dd": True, "twirling": True}, (
        f"Con primitiva = 'sampler' y tecnicas = {{'dd', 'twirling'}} queda {got}."
    )


def test_sampler_rejects_expectation_mitigation():
    for tecnica in ("trex", "zne"):
        got = configured("sampler", [tecnica])
        assert got == "ValueError", (
            f"Con primitiva = 'sampler' y tecnicas = {{{tecnica!r}}} devuelve {got}."
        )


def test_nothing_requested_activates_nothing():
    got = configured("estimator", [])
    assert not got["zne"] and not got["dd"] and not got["twirling"], (
        f"Con primitiva = 'estimator' y tecnicas = set() queda {got}."
    )


def test_only_what_is_requested():
    got = configured("estimator", ["trex"])
    assert got["trex"] is True and not got["zne"] and not got["dd"], (
        f"Con primitiva = 'estimator' y tecnicas = {{'trex'}} queda {got}."
    )
