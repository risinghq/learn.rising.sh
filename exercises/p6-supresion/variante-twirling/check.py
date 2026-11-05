import itertools

from qgcheck import learner, visible

ETIQUETAS = ["".join(p) for p in itertools.product("IXYZ", repeat=2)]


def equals_cx(circuito):
    from qiskit.circuit.library import CXGate
    from qiskit.quantum_info import Operator

    return Operator(circuito).equiv(Operator(CXGate()))


def part_before_cx(circuito):
    """The operation applied to the two qubits before the first CX."""
    from qiskit import QuantumCircuit

    antes = QuantumCircuit(2)
    for inst in circuito.data:
        if inst.operation.name == "cx":
            break
        antes.append(inst.operation, [circuito.find_bit(q).index for q in inst.qubits])
    return antes


@visible("las 16 variantes equivalen a una CX")
def test_equals_cx():
    for etiqueta in ETIQUETAS:
        circuito = learner.variante(etiqueta)
        assert equals_cx(circuito), f"Con antes = '{etiqueta}' el circuito ya no equivale a una CX."


def test_before_is_the_given_pauli():
    import numpy as np
    from qiskit.quantum_info import Operator, Pauli

    for etiqueta in ETIQUETAS:
        antes = Operator(part_before_cx(learner.variante(etiqueta))).data
        pauli = Operator(Pauli(etiqueta)).data
        parecido = round(float(abs(np.trace(pauli.conj().T @ antes)) / 4), 6)
        assert parecido == 1.0, (
            f"Con antes = '{etiqueta}' lo que va antes de la CX se parece a esa Pauli en {parecido}."
        )
