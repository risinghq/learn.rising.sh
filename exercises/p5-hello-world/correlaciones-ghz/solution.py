from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

backend = FakeManilaV2()
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)


def correlaciones(n):
    if not 2 <= n <= backend.num_qubits:
        raise ValueError(f"n debe estar entre 2 y {backend.num_qubits}, los qubits de {backend.name}")
    ghz = QuantumCircuit(n)
    ghz.h(0)
    for i in range(n - 1):
        ghz.cx(i, i + 1)
    isa = pm.run(ghz)
    etiquetas = ["I" * (n - 1 - i) + "Z" + "I" * (i - 1) + "Z" for i in range(1, n)]
    ops = [SparsePauliOp(e).apply_layout(isa.layout) for e in etiquetas]
    estimator = Estimator(mode=backend)
    estimator.options.default_shots = 4000
    estimator.options.simulator.seed_simulator = 7
    evs = estimator.run([(isa, ops)]).result()[0].data.evs
    return {e: round(float(v), 3) for e, v in zip(etiquetas, evs)}


print(correlaciones(2))
