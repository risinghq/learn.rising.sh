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

valores = np.linspace(0, np.pi, 10)[:, None]
observables = SparsePauliOp.from_list([("ZZZ", 1), ("XXX", 1), ("YYY", 1)])

evs_barrido = estimator.run([(circ, observables, valores)]).result()[0].data.evs
print(evs_barrido.shape)
