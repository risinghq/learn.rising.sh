import json

import qiskit.qasm3
from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

backend = FakeManilaV2()
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)

bell = QuantumCircuit(2, 2)
bell.h(0)
bell.cx(0, 1)
bell.measure([0, 1], [0, 1])
isa = pm.run(bell)

qasm = qiskit.qasm3.dumps(isa)

# ✏️ el segundo elemento del PUB son los valores de los parámetros; este circuito no tiene.
# Apuesta qué valor lleva: None, {} o [].
parametros = None
prediccion = "None"

cuerpo_sampler = {
    "program_id": "sampler",
    "backend": "ibm_fez",
    "params": {"pubs": [[qasm, parametros, 500]]},
}
print(json.dumps(cuerpo_sampler["params"]["pubs"][0][1:]))
