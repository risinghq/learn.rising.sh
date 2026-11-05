import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit_addon_obp import backpropagate
from qiskit_addon_utils.slicing import combine_slices, slice_by_gate_types


def retropropaga(capas_absorbidas):
    n, pasos, j, h, dt = 6, 4, 1.0, 0.5, 0.2
    circuito = QuantumCircuit(n)
    for _ in range(pasos):
        for qubit in range(0, n - 1, 2):
            circuito.rzz(2 * j * dt, qubit, qubit + 1)
        for qubit in range(1, n - 1, 2):
            circuito.rzz(2 * j * dt, qubit, qubit + 1)
        for qubit in range(n):
            circuito.rx(2 * h * dt, qubit)
    observable = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    capas = slice_by_gate_types(circuito)
    nuevo, resto, _ = backpropagate(observable, capas[-capas_absorbidas:])
    corto = combine_slices(capas[:-capas_absorbidas] + list(resto), include_barriers=False)
    valor = float(np.real(Statevector(corto).expectation_value(nuevo)))
    return len(nuevo), corto.depth(), valor
