import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

backend = FakeManilaV2()
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)

a, b = Parameter("a"), Parameter("b")
circuito = QuantumCircuit(2)
circuito.rx(a, 0)
circuito.ry(b, 1)
circuito.cx(0, 1)
isa = pm.run(circuito)

# 100 juegos de valores para (a, b): forma (100, 2)
parametros = np.vstack([np.linspace(-np.pi, np.pi, 100), np.linspace(-4 * np.pi, 4 * np.pi, 100)]).T
# 3 observables, cada uno en su propia fila: forma (3, 1)
observables = [
    [SparsePauliOp(["XX", "IY"], [0.5, 0.5])],
    [SparsePauliOp("XX")],
    [SparsePauliOp("IY")],
]
mapeados = [[o.apply_layout(isa.layout) for o in fila] for fila in observables]

estimator = Estimator(mode=backend)
estimator.options.default_shots = 50
estimator.options.simulator.seed_simulator = 7

evs = estimator.run([(isa, mapeados, parametros)]).result()[0].data.evs
print("forma de evs:", evs.shape)

prediccion = (3, 100)
