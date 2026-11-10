from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector


def curvas(n, J, h, dt, pasos):
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    qc = QuantumCircuit(n)
    trotter = [1.0]
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
        trotter.append(float(Statevector(qc).expectation_value(M).real))
    return list(trotter), trotter
