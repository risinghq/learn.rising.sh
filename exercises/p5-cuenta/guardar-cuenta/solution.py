from pathlib import Path

from qiskit_ibm_runtime import QiskitRuntimeService

# Credenciales de práctica: un archivo en esta carpeta y una clave falsa de 44 caracteres.
archivo = str(Path.cwd() / "qiskit-ibm.json")
CLAVE_FALSA = "k" * 44
INSTANCIA = "crn:v1:bluemix:public:quantum-computing:us-east:a/practica:curso::"

QiskitRuntimeService.save_account(
    token=CLAVE_FALSA,
    instance=INSTANCIA,
    name="personal",
    set_as_default=True,
    overwrite=True,
    filename=archivo,
)

guardadas = QiskitRuntimeService.saved_accounts(filename=archivo)
print(sorted(guardadas))

prediccion = "texto plano"
