from qiskit import QuantumCircuit


def bell():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(1, 0)
    return qc
