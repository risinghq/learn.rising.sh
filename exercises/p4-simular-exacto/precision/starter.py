import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp

circuito = QuantumCircuit(2)
circuito.ry(Parameter("theta"), 0)
circuito.h(0)
circuito.cx(0, 1)
observable = SparsePauliOp(["II", "XX", "YY", "ZZ"], coeffs=[1, 1, -1, 1])
valores = [[0], [np.pi / 6], [np.pi / 2]]

exacto = StatevectorEstimator().run([(circuito, observable, valores)]).result()[0].data.evs

precision = 0.5   # ✏️ elige un valor menor

ruidoso = StatevectorEstimator(seed=1).run([(circuito, observable, valores)], precision=precision).result()[0].data.evs
error_max = float(np.abs(ruidoso - exacto).max())
print(ruidoso, f"· error máximo {error_max:.4f}")
