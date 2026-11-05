import math

import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp


def dispersiones(precisiones):
    circuito = QuantumCircuit(2)
    circuito.ry(0.9, 0)
    circuito.cx(0, 1)
    observable = SparsePauliOp("ZZ")
    tabla = {}
    for eps in precisiones:
        valores = [
            StatevectorEstimator(default_precision=eps, seed=seed)
            .run([(circuito, observable)])
            .result()[0]
            .data.evs
            for seed in range(60)
        ]
        tabla[str(eps)] = (math.ceil(1 / eps**2), float(np.std(valores)))
    return tabla
