from qgcheck import learner, state, visible


@visible("Z del qubit 0 en dos qubits")
def test_two_qubits():
    etiquetas = list(learner.z_del_qubit_0(2).paulis.to_labels())
    assert etiquetas == ["IZ"], f"Con n = 2, `z_del_qubit_0` devuelve {etiquetas}."


def test_other_sizes():
    for n in (1, 3, 5):
        etiquetas = list(learner.z_del_qubit_0(n).paulis.to_labels())
        assert etiquetas == ["I" * (n - 1) + "Z"], (
            f"Con n = {n}, `z_del_qubit_0` devuelve {etiquetas}."
        )


def test_value_on_a_state():
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2)
    qc.x(0)
    valor = round(float(state(qc).expectation_value(learner.z_del_qubit_0(2)).real), 6)
    assert valor == -1.0, f"Con n = 2 y el estado |01>, `z_del_qubit_0` mide {valor}."
