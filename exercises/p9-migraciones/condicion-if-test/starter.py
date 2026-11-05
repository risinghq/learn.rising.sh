from qiskit import QuantumCircuit
from qiskit.circuit import ClassicalRegister, QuantumRegister


def x_si_11():
    qr, cr = QuantumRegister(2, "q"), ClassicalRegister(2, "c")
    qc = QuantumCircuit(qr, cr)
    qc.h([0, 1])
    qc.measure(qr, cr)
    # Aplica una X al qubit 0 solo si se midió 11.
    return qc
