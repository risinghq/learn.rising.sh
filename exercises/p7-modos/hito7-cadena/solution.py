from qiskit import QuantumCircuit
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import generate_preset_pass_manager


def cadena(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for q in range(1, n - 1, 2):
            qc.rzz(2 * J * dt, q, q + 1)
        for q in range(0, n - 1, 2):
            qc.rzz(2 * J * dt, q, q + 1)
        for q in range(n):
            qc.rx(2 * h * dt, q)
    return qc


def transpilar(n, J, h, dt, pasos, fraccional):
    base = ["cz", "rz", "sx", "x"] + (["rx", "rzz"] if fraccional else [])
    backend = GenericBackendV2(n, basis_gates=base, seed=1)
    pm = generate_preset_pass_manager(3, backend=backend, scheduling_method="alap", seed_transpiler=1)
    return pm.run(cadena(n, J, h, dt, pasos))
