from qgcheck import inside, learner, visible


@inside
def validar(nombre):
    from qiskit import ClassicalRegister, QuantumCircuit

    qc = QuantumCircuit(3, 3)
    grande = ClassicalRegister(50, "grande")
    qc.add_register(grande)
    if nombre == "simple":
        with qc.if_test((qc.clbits[0], 1)):
            qc.x(1)
    elif nombre == "registro-grande":
        with qc.if_test((grande, 15)):
            qc.x(1)
    elif nombre == "anidado":
        with qc.if_test((qc.clbits[0], 1)):
            with qc.if_test((qc.clbits[1], 1)):
                qc.x(2)
    elif nombre == "medir-dentro":
        with qc.if_test((qc.clbits[0], 1)):
            qc.measure(1, 2)
    elif nombre == "bucle":
        with qc.for_loop(range(2)):
            qc.x(1)
    return {"caso": nombre, "devuelto": learner.es_valido(qc)}


@visible("acepta un if sencillo")
def test_simple_if():
    got = validar("simple")
    assert got["devuelto"] is True, f"Con caso = 'simple', es_valido devuelve {got}."


def test_rejects_invalid_forms():
    for nombre in ("registro-grande", "anidado", "medir-dentro", "bucle"):
        got = validar(nombre)
        assert got["devuelto"] is False, (
            f"Con caso = {nombre!r}, es_valido devuelve {got}."
        )
