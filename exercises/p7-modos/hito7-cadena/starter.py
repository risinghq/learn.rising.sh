from qiskit import QuantumCircuit
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import generate_preset_pass_manager


def cadena(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        pass  # ✏️ las rzz de los enlaces impares y después las de los pares
        for q in range(n):
            qc.rx(2 * h * dt, q)
    return qc


def transpilar(n, J, h, dt, pasos, fraccional):
    base = ["cz", "rz", "sx", "x"]  # ✏️ con fraccional, el backend también acepta rx y rzz
    backend = GenericBackendV2(n, basis_gates=base, seed=1)
    pm = generate_preset_pass_manager(3, backend=backend, scheduling_method="alap", seed_transpiler=1)
    return pm.run(cadena(n, J, h, dt, pasos))
