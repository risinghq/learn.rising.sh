import json

from qgcheck import learner, visible


@visible("el PUB es [texto OpenQASM 3, None, 500]")
def test_pub():
    pub = learner.cuerpo_sampler["params"]["pubs"][0]
    assert pub[0].startswith("OPENQASM 3") and pub[1] is None and pub[2] == 500, (
        f"El PUB lleva {pub[1:]} detrás del circuito."
    )


@visible("tu apuesta coincide con `parametros`")
def test_bet():
    apuesta = learner.prediccion
    real = repr(learner.parametros)
    assert apuesta == real, f"Apostaste {apuesta}, pero `parametros` vale {real}."


def test_body_is_json():
    cuerpo = learner.cuerpo_sampler
    assert json.loads(json.dumps(cuerpo)) == cuerpo, "`cuerpo_sampler` cambia al pasar por JSON."
    assert json.dumps(cuerpo["params"]["pubs"][0][1]) == "null", (
        f"En JSON, `parametros` se envía como {json.dumps(cuerpo['params']['pubs'][0][1])}."
    )
