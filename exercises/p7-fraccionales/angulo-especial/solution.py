from qiskit import QuantumCircuit
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import generate_preset_pass_manager


def conteos_con_angulo(theta_zz):
    circuito = QuantumCircuit(5)
    for _ in range(3):
        for qubit in range(5):
            circuito.rx(0.1, qubit)
        for qubit in range(1, 4, 2):
            circuito.rzz(theta_zz, qubit, qubit + 1)
        for qubit in range(0, 4, 2):
            circuito.rzz(theta_zz, qubit, qubit + 1)
    backend = GenericBackendV2(5, basis_gates=["cz", "rz", "sx", "x"], seed=1)
    isa = generate_preset_pass_manager(3, backend=backend).run(circuito)
    return isa.count_ops().get("cz", 0)
