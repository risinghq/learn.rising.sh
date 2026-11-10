from qiskit import QuantumCircuit


def paso(J, h, dt):
    qc = QuantumCircuit(2)
    qc.rzz(2 * J * dt, 0, 1)
    qc.rx(2 * h * dt, 0)
    qc.rx(2 * h * dt, 1)
    return qc
