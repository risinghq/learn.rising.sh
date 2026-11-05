from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit_addon_obp import backpropagate
from qiskit_addon_utils.slicing import slice_by_gate_types


def mejor_k(limite):
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
    mejor = 0
    for k in range(1, len(capas) + 1):
        nuevo, _, _ = backpropagate(observable, capas[-k:])
        if len(nuevo) > limite:
            break
        mejor = k
    return mejor
