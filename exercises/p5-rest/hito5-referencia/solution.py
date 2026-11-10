import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector


def magnetizacion_referencia(n, J, h, dt, pasos):
    observable = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    valores = []
    for k in range(pasos + 1):
        qc = QuantumCircuit(n)
        for _ in range(k):
            for i in range(n - 1):
                qc.rzz(2 * J * dt, i, i + 1)
            for i in range(n):
                qc.rx(2 * h * dt, i)
        valores.append(float(np.real(Statevector.from_instruction(qc).expectation_value(observable))))
    return valores
