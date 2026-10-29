from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez


def paso(n, J=1.0, h=0.5, dt=0.1):
    qc = QuantumCircuit(n)
    for i in range(n - 1):
        qc.rzz(2 * J * dt, i, i + 1)
    for i in range(n):
        qc.rx(2 * h * dt, i)
    return qc


def trotter(n, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        qc.compose(paso(n), inplace=True)
    return qc


def pasos_max(n, presupuesto):
    # ✏️ tu código aquí
    return 0


print(pasos_max(2, 15))
