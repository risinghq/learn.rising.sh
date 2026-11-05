from qiskit import QuantumCircuit
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import generate_preset_pass_manager


def conteos(n, pasos):
    circuito = QuantumCircuit(n)
    for _ in range(pasos):
        for qubit in range(n):
            circuito.rx(0.1, qubit)
        for qubit in range(1, n - 1, 2):
            circuito.rzz(0.1, qubit, qubit + 1)
        for qubit in range(0, n - 1, 2):
            circuito.rzz(0.1, qubit, qubit + 1)
        circuito.barrier()
    resultado = []
    for basis in (
        ["cz", "rz", "sx", "x"],
        ["cz", "rz", "sx", "x", "rx", "rzz"],
    ):
        backend = GenericBackendV2(n, basis_gates=basis, seed=1)
        isa = generate_preset_pass_manager(
            3, backend=backend, scheduling_method="alap"
        ).run(circuito)
        ops = isa.count_ops()
        resultado.extend((ops.get("cz", 0), ops.get("rzz", 0)))
    return tuple(resultado)
