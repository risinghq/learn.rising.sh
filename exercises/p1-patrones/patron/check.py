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


def ghz(pares):
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(3)
    qc.h(0)
    for control, objetivo in pares:
        qc.cx(control, objetivo)
    return qc


def observable():
    from qiskit.quantum_info import SparsePauliOp

    return SparsePauliOp(["ZZI", "IZZ", "XXX"])


def ideal(qc, obs):
    from qiskit.quantum_info import Statevector

    return float(Statevector(qc).expectation_value(obs).real)


@visible("GHZ de 3 qubits con nivel = 1")
def test_level_one():
    nivel, qc, obs = 1, ghz([(0, 1), (1, 2)]), observable()
    isa, valor = learner.patron(qc, obs, nivel)
    fuera, valor = fuera_del_chip(isa), round(valor, 6)
    assert not fuera and abs(valor - ideal(qc, obs)) < 1e-6, (
        f"Con nivel = {nivel}, `patron` devuelve un circuito con {fuera} fuera del chip y el valor {valor}."
    )


def test_other_levels():
    qc, obs = ghz([(0, 1), (1, 2)]), observable()
    for nivel in (0, 3):
        isa, valor = learner.patron(qc, obs, nivel)
        fuera, valor = fuera_del_chip(isa), round(valor, 6)
        assert not fuera and abs(valor - ideal(qc, obs)) < 1e-6, (
            f"Con nivel = {nivel}, `patron` devuelve un circuito con {fuera} fuera del chip y el valor {valor}."
        )


def test_routing():
    qc, obs = ghz([(0, 1), (0, 2)]), observable()
    for nivel in (1, 3):
        isa, valor = learner.patron(qc, obs, nivel)
        fuera, valor = fuera_del_chip(isa), round(valor, 6)
        assert not fuera and abs(valor - ideal(qc, obs)) < 1e-6, (
            f"Con una CNOT entre los qubits 0 y 2 y nivel = {nivel}, `patron` devuelve un circuito con {fuera} fuera del chip y el valor {valor}."
        )
