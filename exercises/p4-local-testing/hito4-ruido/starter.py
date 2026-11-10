from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer.noise import NoiseModel, depolarizing_error
from qiskit_aer.primitives import EstimatorV2


def trotter(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
    return qc


def curva_ruidosa(n, J, h, dt, pasos, p):
    ruido = NoiseModel()  # ✏️ añade un error despolarizante de dos qubits, con probabilidad p, a cada cx
    pm = generate_preset_pass_manager(1, basis_gates=["cx", "rz", "sx", "x"])
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    circuitos = [pm.run(trotter(n, J, h, dt, k)) for k in range(pasos + 1)]
    estimator = EstimatorV2(options={"backend_options": {"noise_model": ruido}})
    resultado = estimator.run([(c, M) for c in circuitos]).result()
    return [float(r.data.evs) for r in resultado]
