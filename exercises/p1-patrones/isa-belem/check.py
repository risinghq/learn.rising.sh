from qgcheck import learner, visible


def fuera_del_chip(isa):
    from qiskit_ibm_runtime.fake_provider import FakeBelemV2

    backend = FakeBelemV2()
    vecinos = {tuple(arista) for arista in backend.coupling_map.get_edges()}
    fuera = []
    for inst in isa.data:
        qubits = tuple(isa.find_bit(q).index for q in inst.qubits)
        if inst.operation.name not in backend.operation_names:
            fuera.append(inst.operation.name)
        elif len(qubits) == 2 and qubits not in vecinos:
            fuera.append(f"{inst.operation.name} {qubits[0]}-{qubits[1]}")
    return sorted(set(fuera))


def con_cnots(n, pares):
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(n)
    qc.h(0)
    for control, objetivo in pares:
        qc.cx(control, objetivo)
    return qc


@visible("un Bell de 2 qubits queda en puertas del chip")
def test_bell():
    fuera = fuera_del_chip(learner.a_isa(con_cnots(2, [(0, 1)])))
    assert not fuera, f"Con un Bell de 2 qubits, `a_isa` deja fuera del chip {fuera}."


def test_cnot_between_distant_qubits():
    fuera = fuera_del_chip(learner.a_isa(con_cnots(3, [(0, 1), (0, 2)])))
    assert not fuera, f"Con una CNOT entre los qubits 0 y 2, `a_isa` deja fuera del chip {fuera}."


def test_five_qubits():
    fuera = fuera_del_chip(learner.a_isa(con_cnots(5, [(0, 1), (0, 2), (0, 3), (0, 4)])))
    assert not fuera, f"Con un circuito de 5 qubits, `a_isa` deja fuera del chip {fuera}."
