from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_addon_obp import backpropagate
from qiskit_addon_utils.slicing import combine_slices, slice_by_gate_types
from qiskit_ibm_runtime.fake_provider import FakeFez


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


def unir(n, capas):
    return combine_slices(capas, include_barriers=False) if capas else QuantumCircuit(n)


def recortar(n, J, h, dt, pasos, k):
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    capas = slice_by_gate_types(trotter(n, J, h, dt, pasos))
    observable, resto, _ = backpropagate(M, capas[len(capas) - k :])
    return unir(n, capas[: len(capas) - k] + list(resto)), observable


def absorber(n, J, h, dt, pasos):
    pm = generate_preset_pass_manager(optimization_level=1, backend=FakeFez(), seed_transpiler=1)
    completa = pm.run(trotter(n, J, h, dt, pasos)).depth()
    for k in range(1, 3 * pasos + 1):
        corto, observable = recortar(n, J, h, dt, pasos, k)
        if len(observable) <= 100 and pm.run(corto).depth() <= 0.75 * completa:
            return k, corto, observable
    return 0, *recortar(n, J, h, dt, pasos, 0)
