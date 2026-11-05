from qgcheck import learner, visible

CODIGOS = {
    "valor 3": "def valor():\n    return 3\n",
    "valor 4": "def valor():\n    return 4\n",
    "importa execute": "def valor():\n    return 3\n\nfrom qiskit import execute\n",
    "divide entre cero": "def valor():\n    return 1 / 0\n",
}


def veredicto(codigo):
    return "pasa" if learner.pasa(CODIGOS[codigo], 3) else "falla"


@visible("pasa el código con el valor esperado y falla el de otro valor")
def test_right_and_wrong_value():
    got = (veredicto("valor 3"), veredicto("valor 4"))
    assert got == ("pasa", "falla"), (
        f"Con esperado = 3, tu `pasa` dice {got[0]} para `valor 3` y {got[1]} para `valor 4`."
    )


def test_fails_after_defining():
    codigo = "importa execute"
    got = veredicto(codigo)
    assert got == "falla", f"Con el código {codigo!r}, tu `pasa` dice que {got}."


def test_fails_when_called():
    codigo = "divide entre cero"
    got = veredicto(codigo)
    assert got == "falla", f"Con el código {codigo!r}, tu `pasa` dice que {got}."
