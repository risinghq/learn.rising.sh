from qiskit import QuantumCircuit


def paso(J, h, dt):
    qc = QuantumCircuit(2)
    qc.rzz(0.0, 0, 1)
    qc.rx(0.0, 0)
    qc.rx(0.0, 1)
    return qc
