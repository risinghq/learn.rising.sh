import json
from pathlib import Path

from qiskit_ibm_runtime import QiskitRuntimeService

from qgcheck import inside, learner, visible


@inside
def defaults():
    contenido = json.loads(Path(learner.archivo).read_text())
    return [nombre for nombre, cuenta in contenido.items() if cuenta.get("is_default_account")]


@inside
def saved():
    return sorted(QiskitRuntimeService.saved_accounts(filename=learner.archivo))


@visible("solo `clase` es la predeterminada")
def test_clase_is_default():
    nombres = defaults()
    assert nombres == ["clase"], f"En `archivo` las cuentas predeterminadas son {nombres}."


def test_both_accounts_remain():
    nombres = saved()
    assert nombres == ["clase", "personal"], f"En `archivo` quedan guardadas las cuentas {nombres}."
