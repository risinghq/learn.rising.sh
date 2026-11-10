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


def pasos_max(n, J, h, dt, presupuesto):
    pm = generate_preset_pass_manager(3, backend=FakeFez(), seed_transpiler=1)
    mejor = 0
    for pasos in range(1, 11):
        if pm.run(cadena(n, J, h, dt, pasos)).depth() <= presupuesto:
            mejor = pasos
    return mejor
