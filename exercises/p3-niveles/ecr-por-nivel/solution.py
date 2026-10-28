import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import UnitaryGate
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

backend = FakeSherbrooke()


def unitaria_y_swap(semilla):
    azar = np.random.default_rng(semilla)
    q, _ = np.linalg.qr(azar.normal(size=(4, 4)) + 1j * azar.normal(size=(4, 4)))
    qc = QuantumCircuit(2)
    qc.append(UnitaryGate(q), range(2))
    qc.swap(0, 1)
    return qc


def ecr_por_nivel(circuito):
    cuentas = []
    for nivel in range(4):
        pm = generate_preset_pass_manager(nivel, backend=backend, seed_transpiler=12345)
        cuentas.append(pm.run(circuito).count_ops().get("ecr", 0))
    return cuentas


print(ecr_por_nivel(unitaria_y_swap(12345)))
