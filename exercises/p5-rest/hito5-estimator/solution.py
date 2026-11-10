from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2


def trotter(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
    return qc


def ejecutar(n, J, h, dt, pasos, disparos):
    backend = FakeManilaV2()
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1, seed_transpiler=1)
    isas = [pm.run(trotter(n, J, h, dt, k)) for k in range(1, pasos + 1)]
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    observables = [M.apply_layout(isa.layout) for isa in isas]
    estimator = Estimator(mode=backend)
    estimator.options.default_shots = disparos
    estimator.options.simulator.seed_simulator = 5
    resultado = estimator.run(list(zip(isas, observables))).result()
    return [float(pub.data.evs) for pub in resultado]
