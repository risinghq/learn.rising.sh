# Wrong: lowers the degree to 0.5: the circuit does not resemble the unitary.
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import UnitaryGate
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

backend = FakeSherbrooke()

azar = np.random.default_rng(8)
q, _ = np.linalg.qr(azar.normal(size=(4, 4)) + 1j * azar.normal(size=(4, 4)))
qc = QuantumCircuit(2)
qc.append(UnitaryGate(q), range(2))
qc.swap(0, 1)

grado = 0.5   # ✏️ 1.0 es exacto; un valor menor permite aproximar

pm = generate_preset_pass_manager(3, backend=backend, approximation_degree=grado, seed_transpiler=12345)
print("ecr:", pm.run(qc).count_ops().get("ecr", 0))
