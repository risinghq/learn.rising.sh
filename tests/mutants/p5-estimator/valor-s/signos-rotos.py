import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

backend = FakeManilaV2()
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)

# Un Bell con una rotación RY(θ) en el qubit 0, medido con cuatro observables.
theta = Parameter("θ")
chsh = QuantumCircuit(2)
chsh.h(0)
chsh.cx(0, 1)
chsh.ry(theta, 0)
isa = pm.run(chsh)

angulos = np.linspace(0, 2 * np.pi, 13)
ops = [[SparsePauliOp(p).apply_layout(isa.layout)] for p in ["ZZ", "ZX", "XZ", "XX"]]

estimator = Estimator(mode=backend)
estimator.options.default_shots = 300
estimator.options.simulator.seed_simulator = 7

# evs tiene forma (4, 13): filas ZZ, ZX, XZ, XX; columnas, los 13 ángulos.
evs_chsh = estimator.run([(isa, ops, [[t] for t in angulos])]).result()[0].data.evs


def valor_S(evs):
    return evs[0] + evs[1] + evs[2] - evs[3]


S = np.asarray(valor_S(evs_chsh))
print(f"|S| máximo: {np.abs(S).max():.2f}")
