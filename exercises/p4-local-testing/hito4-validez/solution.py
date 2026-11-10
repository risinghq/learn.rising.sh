import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer.noise import NoiseModel, depolarizing_error
from qiskit_aer.primitives import EstimatorV2
from scipy.linalg import expm


def trotter(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
    return qc


def curva_ruidosa(n, J, h, dt, pasos, p):
    ruido = NoiseModel()
    ruido.add_all_qubit_quantum_error(depolarizing_error(p, 2), ["cx"])
    pm = generate_preset_pass_manager(1, basis_gates=["cx", "rz", "sx", "x"])
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    circuitos = [pm.run(trotter(n, J, h, dt, k)) for k in range(pasos + 1)]
    estimator = EstimatorV2(options={"backend_options": {"noise_model": ruido}})
    resultado = estimator.run([(c, M) for c in circuitos]).result()
    return [float(r.data.evs) for r in resultado]


def curva_exacta(n, J, h, dt, pasos):
    terminos = [("ZZ", [i, i + 1], J) for i in range(n - 1)] + [("X", [i], h) for i in range(n)]
    U = expm(-1j * dt * SparsePauliOp.from_sparse_list(terminos, num_qubits=n).to_matrix())
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    psi = Statevector.from_label("0" * n)
    valores = []
    for _ in range(pasos + 1):
        valores.append(float(psi.expectation_value(M).real))
        psi = psi.evolve(U)
    return valores


def tiempo_de_validez(n, J, h, dt, pasos, p, tol):
    ruidosa = curva_ruidosa(n, J, h, dt, pasos, p)
    exacta = curva_exacta(n, J, h, dt, pasos)
    for k in range(pasos + 1):
        if abs(ruidosa[k] - exacta[k]) > tol:
            return k * dt
    return None
