from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit_aer.noise import NoiseModel, depolarizing_error
from qiskit_aer.primitives import EstimatorV2


def curva_ruidosa(n, J, h, dt, pasos, p):
    ruido = NoiseModel()
    ruido.add_all_qubit_quantum_error(depolarizing_error(p, 2), ["cx"])
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    circuitos = []
    for k in range(pasos + 1):
        qc = QuantumCircuit(n)
        for _ in range(k):
            for i in range(n - 1):
                qc.rzz(2 * J * dt, i, i + 1)
            for i in range(n):
                qc.rx(2 * h * dt, i)
        circuitos.append(qc)
    estimator = EstimatorV2(options={"backend_options": {"noise_model": ruido}})
    resultado = estimator.run([(c, M) for c in circuitos]).result()
    return [float(r.data.evs) for r in resultado]
