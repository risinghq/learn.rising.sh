from pathlib import Path

from qiskit_ibm_runtime import QiskitRuntimeService

# Credenciales de práctica: un archivo en esta carpeta y una clave falsa de 44 caracteres.
archivo = str(Path.cwd() / "qiskit-ibm.json")
CLAVE_FALSA = "k" * 44
INSTANCIA = "crn:v1:bluemix:public:quantum-computing:us-east:a/practica:curso::"

# ✏️ guarda aquí la cuenta "personal" con QiskitRuntimeService.save_account

guardadas = QiskitRuntimeService.saved_accounts(filename=archivo)
print(sorted(guardadas))

# ✏️ apuesta: ¿la clave queda "cifrada" o en "texto plano"?
prediccion = ""
