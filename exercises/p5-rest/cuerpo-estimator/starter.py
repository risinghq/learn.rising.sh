import qiskit.qasm3
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

backend = FakeManilaV2()
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)

bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)
isa = pm.run(bell)


def cuerpo_estimator(isa, observable, opciones):
    return {}   # ✏️ program_id, backend, params con pubs y options


opciones_zne = {"resilience": {"zne_mitigation": True, "zne": {"noise_factors": [1, 3, 5]}}}
cuerpo = cuerpo_estimator(isa, SparsePauliOp("ZZ"), opciones_zne)
print(cuerpo.get("params", {}).get("pubs", [[None, None]])[0][1:])
