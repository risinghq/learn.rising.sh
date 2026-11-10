import numpy as np
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


def plegar(qc, k):
    out = qc.copy()
    for _ in range(k):
        out.compose(qc.inverse(), inplace=True)
        out.compose(qc, inplace=True)
    return out


def extrapolar(factores, valores):
    pendiente, ordenada = np.polyfit(factores, np.log(valores), 1)
    return float(np.exp(ordenada))


def zne(n, J, h, dt, pasos, p):
    ruido = NoiseModel()
    ruido.add_all_qubit_quantum_error(depolarizing_error(p, 2), ["cx"])
    pm = generate_preset_pass_manager(1, basis_gates=["cx", "rz", "sx", "x"])
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    base = trotter(n, J, h, dt, pasos)
    circuitos = [pm.run(plegar(base, k)) for k in (0, 1, 2)]
    estimator = EstimatorV2(options={"backend_options": {"noise_model": ruido}})
    valores = [float(r.data.evs) for r in estimator.run([(c, M) for c in circuitos]).result()]
    return valores[0], extrapolar([1, 3, 5], valores)
