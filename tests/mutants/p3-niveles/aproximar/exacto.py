# Wrong: leaves the degree at 1.0.
from qiskit import QuantumCircuit
from qiskit.circuit.library import UnitaryGate
from qiskit.quantum_info import random_unitary
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

backend = FakeSherbrooke()

qc = QuantumCircuit(2)
qc.append(UnitaryGate(random_unitary(4, seed=99)), range(2))
qc.swap(0, 1)

grado = 1.0   # ✏️ 1.0 es exacto; un valor menor permite aproximar

pm = generate_preset_pass_manager(3, backend=backend, approximation_degree=grado, seed_transpiler=12345)
print("ecr:", pm.run(qc).count_ops().get("ecr", 0))
