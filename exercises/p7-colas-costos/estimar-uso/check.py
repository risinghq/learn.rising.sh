from qgcheck import inside, learner, visible


@inside
def uso(qubits, ejecuciones):
    from qiskit import QuantumCircuit
    from qiskit_ibm_runtime.fake_provider import FakeFez

    qc = QuantumCircuit(qubits)
    qc.h(0)
    for qubit in range(qubits - 1):
        qc.cx(qubit, qubit + 1)
    qc.measure_all()
    return learner.estimar_uso(FakeFez(), qc, ejecuciones)


@visible("estima el Bell como la misión")
def test_bell():
    got = uso(2, 4096)
    assert got == 4, f"Con qubits = 2 y ejecuciones = 4096, devuelve {got}."


def test_larger_circuit_costs_more():
    got = uso(5, 100_000)
    assert got > 4, f"Con qubits = 5 y ejecuciones = 100000, devuelve {got}."
