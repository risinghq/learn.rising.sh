from qgcheck import inside, learner, visible


@inside
def options(perfil):
    o = learner.crear_estimator(perfil).options
    return dict(
        resiliencia=o.resilience_level,
        desacoplamiento=bool(o.dynamical_decoupling.enable),
        secuencia=o.dynamical_decoupling.sequence_type,
        puertas=bool(o.twirling.enable_gates),
        mediciones=bool(o.twirling.enable_measure),
        disparos=o.default_shots,
    )


@visible("el perfil `crudo` no corrige nada")
def test_raw():
    o = options("crudo")
    limpio = o["resiliencia"] == 0 and not (o["desacoplamiento"] or o["puertas"] or o["mediciones"])
    assert limpio, f"Con perfil = 'crudo' las opciones son {o}."


@visible("el perfil `protegido` usa XY4 y twirling de puertas y de mediciones")
def test_protected():
    o = options("protegido")
    protegido = o["desacoplamiento"] and o["secuencia"] == "XY4" and o["puertas"] and o["mediciones"]
    assert protegido, f"Con perfil = 'protegido' las opciones son {o}."


def test_shots_are_kept():
    for perfil in ("crudo", "protegido"):
        disparos = options(perfil)["disparos"]
        assert disparos == 4000, f"Con perfil = {perfil!r} `default_shots` vale {disparos}."
