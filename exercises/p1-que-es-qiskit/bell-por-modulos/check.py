from qgcheck import gates, learner, operator, state, visible

BASE = {"rz", "sx", "cz"}


def redondeado(probabilidades):
    return {str(k): round(float(v), 6) for k, v in probabilidades.items()}


def ghz(n):
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(n)
    qc.h(0)
    for k in range(n - 1):
        qc.cx(k, k + 1)
    return qc


def estrella():
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(0, 2)
    return qc


def lejanas(circuito):
    return [
        inst.operation.name
        for inst in circuito.data
        if len(inst.qubits) == 2
        and abs(circuito.find_bit(inst.qubits[0]).index - circuito.find_bit(inst.qubits[1]).index)
        != 1
    ]


@visible("`bell()` da probabilidad 1/2 a 00 y a 11")
def test_bell_probabilities():
    got = redondeado(state(learner.bell()).probabilities_dict())
    assert got == {"00": 0.5, "11": 0.5}, f"`bell()` da las probabilidades {got}."


@visible("`probabilidades` de un GHZ de 3 qubits")
def test_probabilities_of_ghz():
    qc = ghz(3)
    got = redondeado(learner.probabilidades(qc))
    assert got == {"000": 0.5, "111": 0.5}, (
        f"Con un GHZ de 3 qubits, `probabilidades` devuelve {got}."
    )


@visible("`a_base` deja solo rz, sx y cz")
def test_basis_gates():
    qc = ghz(2)
    qc.measure_all()
    usadas = sorted(set(gates(learner.a_base(qc))) - {"measure", "barrier"})
    assert set(usadas) <= BASE, f"Con un Bell de 2 qubits, `a_base` deja las puertas {usadas}."


def test_bell_phase():
    from qiskit.quantum_info import Statevector

    bell = Statevector([1, 0, 0, 1]) / 2**0.5
    fase = "con la fase de Bell" if state(learner.bell()).equiv(bell) else "con otra fase"
    assert fase == "con la fase de Bell", f"`bell()` prepara el estado {fase}."


def test_unbalanced_state():
    from math import pi

    from qiskit import QuantumCircuit

    qc = QuantumCircuit(1)
    qc.ry(2 * pi / 3, 0)
    got = redondeado(learner.probabilidades(qc))
    assert got == {"0": 0.25, "1": 0.75}, (
        f"Con un solo qubit en ry(2π/3), `probabilidades` devuelve {got}."
    )


def test_connectivity():
    qc = estrella()
    salida = learner.a_base(qc)
    usadas = sorted(set(gates(salida)) - {"measure", "barrier"})
    separadas = lejanas(salida)
    assert set(usadas) <= BASE and not separadas, (
        f"Con una estrella de 3 qubits, `a_base` deja las puertas {usadas} y {separadas} entre qubits no vecinos."
    )


def test_same_operation():
    qc = estrella()
    salida = learner.a_base(qc)
    from qiskit.quantum_info import Operator

    resultado = "la misma operación" if operator(salida).equiv(Operator(qc)) else "otra operación"
    assert resultado == "la misma operación", (
        f"Con una estrella de 3 qubits, `a_base` deja {resultado}."
    )
