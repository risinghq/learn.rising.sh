from qiskit import QuantumCircuit


def correccion():
    qc = QuantumCircuit(1, 2)
    qc.h(0)
    # Construye aquí la medición intermedia, el if y la medición final.
    return qc
