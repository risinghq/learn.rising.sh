from qiskit import QuantumCircuit


def paso(n, J, h, dt):
    qc = QuantumCircuit(n)
    for i in range(n - 1):
        qc.rzz(2 * J * dt, i, i + 1)
    for i in range(n):
        qc.rx(2 * h * dt, i)
    return qc


def trotter(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        qc.compose(paso(n, J, h, dt), inplace=True)
    return qc
