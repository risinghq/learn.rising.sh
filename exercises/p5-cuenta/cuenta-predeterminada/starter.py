import json
from pathlib import Path

from qiskit_ibm_runtime import QiskitRuntimeService

archivo = str(Path.cwd() / "qiskit-ibm.json")
CLAVE_FALSA = "k" * 44

QiskitRuntimeService.save_account(
    token=CLAVE_FALSA, name="personal", set_as_default=True, overwrite=True, filename=archivo
)
# Esta segunda cuenta debería ser la predeterminada de QiskitRuntimeService().
QiskitRuntimeService.save_account(
    token=CLAVE_FALSA, name="clase", set_as_default=False, overwrite=True, filename=archivo
)

contenido = json.loads(Path(archivo).read_text())
predeterminadas = [nombre for nombre, cuenta in contenido.items() if cuenta.get("is_default_account")]
print("Predeterminadas:", predeterminadas)
