from qgcheck import inside, learner, visible


@inside
def operaciones():
    return {str(k): int(v) for k, v in learner.x_si_11().count_ops().items()}


@inside
def condicion():
    qc = learner.x_si_11()
    op = qc.data[-1].operation
    if op.name != "if_else":
        return "sin if_else"
    return f"valor {op.condition[1]}"


@inside
def cuerpo():
    qc = learner.x_si_11()
    inst = qc.data[-1]
    if inst.operation.name != "if_else":
        return "sin if_else"
    puertas = [i.operation.name for i in inst.operation.blocks[0].data]
    qubits = [qc.find_bit(q).index for q in inst.qubits]
    return f"{puertas} en los qubits {qubits}"


@visible("la condición es una sola instrucción `if_else`")
def test_one_if_else():
    got = operaciones()
    assert got == {"h": 2, "measure": 2, "if_else": 1}, f"`x_si_11()` tiene las operaciones {got}."


def test_condition_value():
    got = condicion()
    assert got == "valor 3", f"`x_si_11()` compara el registro con: {got}."


def test_body():
    got = cuerpo()
    assert got == "['x'] en los qubits [0]", f"El bloque de `x_si_11()` tiene {got}."
