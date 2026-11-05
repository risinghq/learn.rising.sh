from qiskit import QuantumCircuit


def correccion():
    qc = QuantumCircuit(1, 2)
    qc.h(0)
    qc.measure(0, 0)
    with qc.if_test((qc.clbits[0], 1)):
        qc.x(0)
    qc.measure(0, 1)
    return qc
