import json
from pathlib import Path

from qiskit_ibm_runtime import QiskitRuntimeService

from qgcheck import inside, learner, visible


@inside
def saved():
    return QiskitRuntimeService.saved_accounts(filename=learner.archivo)


@inside
def defaults():
    contenido = json.loads(Path(learner.archivo).read_text())
    return [nombre for nombre, cuenta in contenido.items() if cuenta.get("is_default_account")]


@visible("la cuenta `personal` queda guardada con su instancia")
def test_saved():
    cuentas = saved()
    assert "personal" in cuentas, f"En `archivo` hay las cuentas {sorted(cuentas)}: falta `personal`."
    assert cuentas["personal"].get("instance") == learner.INSTANCIA, "La cuenta `personal` no guarda la `INSTANCIA`."


@visible("tu apuesta coincide con lo que guarda el archivo")
def test_bet():
    cuentas = saved()
    assert "personal" in cuentas, "Primero guarda la cuenta `personal`."
    real = "texto plano" if cuentas["personal"]["token"] == learner.CLAVE_FALSA else "cifrada"
    assert learner.prediccion == real, f"Apostaste {learner.prediccion!r}, pero la clave del archivo está {real}."


def test_default():
    nombres = defaults()
    assert nombres == ["personal"], f"En `archivo` las cuentas predeterminadas son {nombres}."
