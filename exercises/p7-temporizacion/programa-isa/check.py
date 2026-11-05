from qgcheck import inside, learner, visible


@inside
def filas(n):
    from qiskit import QuantumCircuit
    from qiskit.providers.fake_provider import GenericBackendV2
    from qiskit.transpiler import generate_preset_pass_manager

    basis = ["rz", "sx", "x"] if n == 1 else ["cz", "rz", "sx", "x"]
    backend = GenericBackendV2(n, basis_gates=basis, seed=1)
    qc = QuantumCircuit(n)
    qc.h(0)
    if n > 1:
        qc.cx(0, 1)
    isa = generate_preset_pass_manager(
        1, backend=backend, scheduling_method="alap"
    ).run(qc)
    got = learner.programacion(isa, backend)
    return len(got), len(isa.data), max((i + d for _, _, i, d in got), default=0)


@visible("programa todas las instrucciones del Bell")
def test_two_qubits():
    got = filas(2)
    assert got[0] == got[1] and got[2] > 0, f"Con n = 2, programacion devuelve {got}."


def test_one_qubit():
    got = filas(1)
    assert got[0] == got[1] and got[2] > 0, f"Con n = 1, programacion devuelve {got}."
