from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez


def cadena(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
    return qc


def profundidades(n, J, h, dt, pasos):
    qc = cadena(n, J, h, dt, pasos)
    backend = FakeFez()
    return {
        str(nivel): generate_preset_pass_manager(nivel, backend=backend, seed_transpiler=1).run(qc).depth()
        for nivel in range(4)
    }
