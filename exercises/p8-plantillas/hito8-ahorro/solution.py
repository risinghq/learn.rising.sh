from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit_addon_obp import backpropagate
from qiskit_addon_obp.utils.simplify import OperatorBudget
from qiskit_addon_utils.slicing import combine_slices, slice_by_gate_types


def trotter(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for a in range(0, n - 1, 2):
            qc.rzz(2 * J * dt, a, a + 1)
        for a in range(1, n - 1, 2):
            qc.rzz(2 * J * dt, a, a + 1)
        for a in range(n):
            qc.rx(2 * h * dt, a)
    return qc


def ahorro(n, J, h, dt, pasos, limite):
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    capas = slice_by_gate_types(trotter(n, J, h, dt, pasos))
    observable, resto, _ = backpropagate(M, capas, operator_budget=OperatorBudget(max_paulis=limite))
    corto = combine_slices(list(resto), include_barriers=False) if resto else QuantumCircuit(n)
    return corto, observable
