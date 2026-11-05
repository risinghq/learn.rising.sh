import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit_addon_obp import backpropagate
from qiskit_addon_utils.slicing import combine_slices, slice_by_gate_types


def terminos_con_presupuesto(limite):
    circuito = QuantumCircuit(6)
    for _ in range(4):
        for qubit in range(0, 5, 2):
            circuito.rzz(0.4, qubit, qubit + 1)
        for qubit in range(1, 5, 2):
            circuito.rzz(0.4, qubit, qubit + 1)
        for qubit in range(6):
            circuito.rx(0.2, qubit)
    observable = SparsePauliOp.from_sparse_list([("Z", [i], 1 / 6) for i in range(6)], num_qubits=6)
    capas = slice_by_gate_types(circuito)
    presupuesto = None
    nuevo, resto, _ = backpropagate(observable, capas, operator_budget=presupuesto)
    corto = combine_slices(resto, include_barriers=False) if resto else QuantumCircuit(6)
    valor = float(np.real(Statevector(corto).expectation_value(nuevo)))
    return len(nuevo), corto.depth(), valor
