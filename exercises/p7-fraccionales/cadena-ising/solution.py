from qiskit import QuantumCircuit


def cadena_ising(n, pasos, theta_x, theta_zz):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for qubit in range(n):
            qc.rx(theta_x, qubit)
        for qubit in range(1, n - 1, 2):
            qc.rzz(theta_zz, qubit, qubit + 1)
        for qubit in range(0, n - 1, 2):
            qc.rzz(theta_zz, qubit, qubit + 1)
        qc.barrier()
    return qc
