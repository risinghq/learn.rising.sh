from qgcheck import learner, visible


def transpilar(qc, layout):
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime.fake_provider import FakeBelemV2

    pm = generate_preset_pass_manager(
        optimization_level=1, backend=FakeBelemV2(), initial_layout=layout
    )
    return pm.run(qc)


def ideal(qc, obs):
    from qiskit.quantum_info import Statevector

    return float(Statevector(qc).expectation_value(obs).real)


def bell():
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    return qc


@visible("el observable sigue al qubit 0 al otro lado del layout")
def test_layout_is_applied():
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp

    qc = QuantumCircuit(2)
    qc.x(0)
    obs = SparsePauliOp("IZ")
    got = round(learner.valor_ideal(transpilar(qc, [4, 3]), obs), 6)
    assert abs(got - ideal(qc, obs)) < 1e-6, (
        f"Con el observable IZ y el qubit 0 en el qubit físico 4, `valor_ideal` devuelve {got}."
    )


def test_all_terms():
    from qiskit.quantum_info import SparsePauliOp

    qc = bell()
    for etiquetas in (["ZZ", "XX"], ["ZZ", "XX", "YY"]):
        obs = SparsePauliOp(etiquetas)
        got = round(learner.valor_ideal(transpilar(qc, [2, 1]), obs), 6)
        assert abs(got - ideal(qc, obs)) < 1e-6, (
            f"Con el observable {etiquetas}, `valor_ideal` devuelve {got}."
        )


def test_three_qubits_with_a_layout():
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp

    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 1)
    qc.x(2)
    obs = SparsePauliOp(["ZZI", "IIZ", "XXI"])
    got = round(learner.valor_ideal(transpilar(qc, [4, 3, 1]), obs), 6)
    assert abs(got - ideal(qc, obs)) < 1e-6, (
        f"Con un circuito de 3 qubits en los qubits físicos 4, 3 y 1, `valor_ideal` devuelve {got}."
    )
