import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp

circ = QuantumCircuit(3)
circ.ry(Parameter("a"), 0)
circ.cx(0, 1)
circ.cx(1, 2)
estimator = StatevectorEstimator()

obs_uno_a_uno = [SparsePauliOp(p) for p in ["III", "XXX", "YYY", "ZZZ", "XYZ"]]
uno_a_uno = estimator.run([(circ, obs_uno_a_uno, np.linspace(0, 1, 5)[:, None])]).result()[0].data.evs

obs_columna = [[SparsePauliOp(p)] for p in ["III", "XXX", "YYY", "ZZZ"]]
producto = estimator.run([(circ, obs_columna, np.linspace(0, 1, 6)[None, :, None])]).result()[0].data.evs

prediccion = None   # ✏️ tu apuesta: las formas de uno_a_uno y de producto, como ((...), (...))
# compruébalo con print(uno_a_uno.shape, producto.shape)
