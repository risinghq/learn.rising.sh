from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister


def circuito(bits):
    cr = ClassicalRegister(2, "cr")
    extra = ClassicalRegister(1, "res")
    qc = QuantumCircuit(QuantumRegister(3), cr, extra)
    if bits & 1:
        qc.x(0)
    if bits & 2:
        qc.x(1)
    qc.measure([0, 1], cr)
    with qc.if_test((cr, 0b11)):
        qc.x(2)
    qc.measure(2, 2)
    return qc
