from qgcheck import learner, visible


def leer(texto):
    from qiskit import qasm2

    try:
        return qasm2.loads(texto)
    except Exception:
        return None


def estado(texto):
    from qiskit.quantum_info import Statevector

    qc = leer(texto)
    if qc is None:
        return None
    return Statevector(qc.remove_final_measurements(inplace=False))


@visible("el programa deja solo 00 y 11 con probabilidad 1/2")
def test_probabilities():
    texto = learner.programa_bell()
    sv = estado(texto)
    got = (
        "un programa que Qiskit no lee"
        if sv is None
        else {str(k): round(float(v), 6) for k, v in sv.probabilities_dict().items()}
    )
    assert got == {"00": 0.5, "11": 0.5}, f"`programa_bell` prepara {got}."


def test_custom_gate_is_one_instruction():
    qc = leer(learner.programa_bell())
    ops = {} if qc is None else dict(qc.count_ops())
    got = (
        "con la puerta `bell` como instrucción"
        if ops.get("bell") == 1
        else f"con las instrucciones {sorted(ops)}"
    )
    assert got == "con la puerta `bell` como instrucción", f"`programa_bell` queda {got}."


def test_bell_phase():
    from qiskit.quantum_info import Statevector

    sv = estado(learner.programa_bell())
    bell = Statevector([1, 0, 0, 1]) / 2**0.5
    got = "con la fase de Bell" if sv is not None and sv.equiv(bell) else "con otra fase"
    assert got == "con la fase de Bell", f"`programa_bell` prepara el estado {got}."


def test_measures_both_qubits():
    qc = leer(learner.programa_bell())
    medidos = 0 if qc is None else dict(qc.count_ops()).get("measure", 0)
    assert medidos == 2, f"`programa_bell` mide {medidos} qubits."
