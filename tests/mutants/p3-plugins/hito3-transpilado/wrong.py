from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez


def circuito(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(0.2, i, i + 1)
        for i in range(n):
            qc.rx(0.1, i)
    return generate_preset_pass_manager(3, backend=FakeFez(), seed_transpiler=1).run(qc)
