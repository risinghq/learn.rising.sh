from qgcheck import learner, visible


CRUDO = """main,rz_0,Qubit 0,1393,0,shift_phase
main,sx_0,Qubit 0,1393,9,play
main,measure_0,Qubit 0,1402,64,play
main,measure_0,AWGR0_0,1523,325,capture"""


@visible("lee cuatro líneas y convierte los números")
def test_lesson_lines():
    got = learner.leer(CRUDO)
    assert len(got) == 4 and got[0]["inicio"] == 1393 and got[-1]["duracion"] == 325, (
        f"Con las líneas de la lección, `leer` devuelve {got}."
    )


def test_other_line():
    texto = "rama,pulso,canal,7,11,play"
    got = learner.leer(texto)
    assert got == [
        {
            "rama": "rama",
            "instruccion": "pulso",
            "canal": "canal",
            "inicio": 7,
            "duracion": 11,
            "pulso": "play",
        }
    ], f"Con texto = {texto!r}, `leer` devuelve {got}."
