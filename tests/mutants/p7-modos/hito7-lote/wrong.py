from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime import Batch
from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.fake_provider import FakeBelemV2


def cadena(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for q in range(1, n - 1, 2):
            qc.rzz(2 * J * dt, q, q + 1)
        for q in range(0, n - 1, 2):
            qc.rzz(2 * J * dt, q, q + 1)
        for q in range(n):
            qc.rx(2 * h * dt, q)
    return qc


def lote(n, J, h, dt, pasos):
    backend = FakeBelemV2()
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1, seed_transpiler=1)
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    with Batch(backend=backend) as sesion:
        estimator = Estimator(mode=sesion)
        estimator.options.simulator.seed_simulator = 5
        trabajos = []
        for k in range(1, pasos + 1):
            isa = pm.run(cadena(n, J, h, dt, k))
            trabajos.append(float(Statevector(cadena(n, J, h, dt, k)).expectation_value(M).real))
        return trabajos
