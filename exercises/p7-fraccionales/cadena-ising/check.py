from qgcheck import learner, visible


@visible("dos pasos en cuatro qubits")
def test_four_qubits():
    qc = learner.cadena_ising(4, 2, 0.1, 0.2)
    assert qc.count_ops().get("rx") == 8 and qc.count_ops().get("rzz") == 6, (
        f"Con n = 4 y pasos = 2, la cadena devuelve {qc.count_ops()}."
    )


def test_six_qubits():
    qc = learner.cadena_ising(6, 3, 0.2, 0.4)
    got = (qc.count_ops().get("rx", 0), qc.count_ops().get("rzz", 0))
    assert got == (18, 15), f"Con n = 6 y pasos = 3, devuelve {got}."
