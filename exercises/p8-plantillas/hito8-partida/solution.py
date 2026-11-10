import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez
from scipy.linalg import expm


def trotter(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for a in range(0, n - 1, 2):
            qc.rzz(2 * J * dt, a, a + 1)
        for a in range(1, n - 1, 2):
            qc.rzz(2 * J * dt, a, a + 1)
        for a in range(n):
            qc.rx(2 * h * dt, a)
    return qc


def partida(n, J, h, dt, pasos):
    H = SparsePauliOp.from_sparse_list(
        [("ZZ", [i, i + 1], J) for i in range(n - 1)] + [("X", [i], h) for i in range(n)], num_qubits=n
    )
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    psi = np.zeros(2**n, dtype=complex)
    psi[0] = 1
    psi = expm(-1j * H.to_matrix() * dt * pasos) @ psi
    circuito = trotter(n, J, h, dt, pasos)
    pm = generate_preset_pass_manager(optimization_level=1, backend=FakeFez(), seed_transpiler=1)
    return {
        "exacta": float(np.real(np.vdot(psi, M.to_matrix() @ psi))),
        "trotter": float(np.real(Statevector(circuito).expectation_value(M))),
        "profundidad": pm.run(circuito).depth(),
    }
