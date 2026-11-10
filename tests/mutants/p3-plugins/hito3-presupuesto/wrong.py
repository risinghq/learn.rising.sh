from qiskit import QuantumCircuit


def pasos_max(n, J, h, dt, presupuesto):
    mejor = 0
    for pasos in range(1, 11):
        qc = QuantumCircuit(n)
        for _ in range(pasos):
            for i in range(n - 1):
                qc.rzz(2 * J * dt, i, i + 1)
            for i in range(n):
                qc.rx(2 * h * dt, i)
        if qc.depth() <= presupuesto:
            mejor = pasos
    return mejor
