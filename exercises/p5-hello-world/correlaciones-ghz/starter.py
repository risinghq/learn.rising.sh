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
    # ✏️ H en el qubit 0 y una cadena de CNOT
    isa = pm.run(ghz)
    etiquetas = ["I" * n]   # ✏️ una etiqueta por cada i = 1…n-1, con Z en los qubits 0 e i
    ops = [SparsePauliOp(e).apply_layout(isa.layout) for e in etiquetas]
    estimator = Estimator(mode=backend)
    estimator.options.default_shots = 4000
    estimator.options.simulator.seed_simulator = 7
    evs = estimator.run([(isa, ops)]).result()[0].data.evs
    return {e: round(float(v), 3) for e, v in zip(etiquetas, evs)}


print(correlaciones(2))
