from qgcheck import learner, visible


def circuito(nombre):
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(3 if nombre == "ghz" else 2)
    if nombre == "ry":
        qc.ry(0.7, 0)
        qc.cx(0, 1)
        return qc
    qc.h(0)
    qc.cx(0, 1)
    if nombre == "ghz":
        qc.cx(1, 2)
    return qc


def por_estimator(qc, obs):
    from qiskit.primitives import StatevectorEstimator

    return float(StatevectorEstimator().run([(qc, obs)]).result()[0].data.evs)


@visible("Bell con ZZ, XX y YY")
def test_bell():
    from qiskit.quantum_info import SparsePauliOp

    qc = circuito("bell")
    for etiqueta in ("ZZ", "XX", "YY", "IZ"):
        obs = SparsePauliOp(etiqueta)
        got = round(learner.valor_esperado(qc, obs), 6)
        assert abs(got - por_estimator(qc, obs)) < 1e-6, (
            f"Con el estado de Bell y el observable {etiqueta}, `valor_esperado` devuelve {got}."
        )


def test_three_qubits():
    from qiskit.quantum_info import SparsePauliOp

    qc = circuito("ghz")
    for etiqueta in ("XXX", "IZZ", "ZIZ"):
        obs = SparsePauliOp(etiqueta)
        got = round(learner.valor_esperado(qc, obs), 6)
        assert abs(got - por_estimator(qc, obs)) < 1e-6, (
            f"Con un GHZ de 3 qubits y el observable {etiqueta}, `valor_esperado` devuelve {got}."
        )


def test_rotated_state():
    from qiskit.quantum_info import SparsePauliOp

    qc = circuito("ry")
    for etiqueta in ("IZ", "ZZ", "XX"):
        obs = SparsePauliOp(etiqueta)
        got = round(learner.valor_esperado(qc, obs), 6)
        assert abs(got - por_estimator(qc, obs)) < 1e-6, (
            f"Con un estado ry(0.7) y el observable {etiqueta}, `valor_esperado` devuelve {got}."
        )


def test_several_terms():
    from qiskit.quantum_info import SparsePauliOp

    qc = circuito("ry")
    obs = SparsePauliOp(["ZZ", "XX", "IZ"], [1.0, 0.5, -2.0])
    got = round(learner.valor_esperado(qc, obs), 6)
    assert abs(got - por_estimator(qc, obs)) < 1e-6, (
        f"Con un observable de tres términos con coeficientes, `valor_esperado` devuelve {got}."
    )
