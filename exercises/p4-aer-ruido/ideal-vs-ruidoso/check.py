from qgcheck import learner, visible


@visible("tu apuesta es la fracción correcta con ruido")
def test_bet():
    bet, real = learner.prediccion, learner.ruidoso
    assert isinstance(bet, (int, float)) and abs(bet - real) <= 0.04, (
        "Tu apuesta está lejos de la fracción de disparos correctos con ruido. Cuenta las 5 CX del GHZ de 6 qubits y piensa cuánto pierde cada una.")


def test_same_noise():
    ideal, ruidoso = round(learner.ideal, 3), round(learner.ruidoso, 3)
    assert ideal == 1.0 and 0.85 < ruidoso < 1.0, (
        f"`ideal` vale {ideal} y `ruidoso` vale {ruidoso}; el circuito o el ruido de la lección cambiaron.")
