from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector


def trotter(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
    return qc


def ejecutar(n, J, h, dt, pasos, disparos):
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    return [float(Statevector(trotter(n, J, h, dt, k)).expectation_value(M).real) for k in range(1, pasos + 1)]
