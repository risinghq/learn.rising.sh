from qgcheck import learner, visible


def leer(texto):
    from qiskit import qasm2

    try:
        return qasm2.loads(texto)
    except Exception:
        return None


def probabilidades(texto):
    from qiskit.quantum_info import Statevector

    qc = leer(texto)
    if qc is None:
        return "un programa que Qiskit no lee"
    sv = Statevector(qc)
    return {str(k): round(float(v), 6) for k, v in sv.probabilities_dict().items()}


def ghz_de(n):
    return {"0" * n: 0.5, "1" * n: 0.5}


@visible("con n = 3 quedan solo 000 y 111")
def test_three_qubits():
    n = 3
    got = probabilidades(learner.programa_ghz(n))
    assert got == ghz_de(n), f"Con n = {n}, `programa_ghz` prepara {got}."


def test_other_sizes():
    for n in (2, 5):
        got = probabilidades(learner.programa_ghz(n))
        assert got == ghz_de(n), f"Con n = {n}, `programa_ghz` prepara {got}."


def test_custom_gate_is_one_instruction():
    n = 4
    qc = leer(learner.programa_ghz(n))
    ops = {} if qc is None else dict(qc.count_ops())
    got = (
        "con la puerta `ghz` como instrucción"
        if ops.get("ghz") == 1
        else f"con las instrucciones {sorted(ops)}"
    )
    assert got == "con la puerta `ghz` como instrucción", (
        f"Con n = {n}, `programa_ghz` queda {got}."
    )


def test_ghz_phase():
    from qiskit.quantum_info import Statevector

    n = 4
    qc = leer(learner.programa_ghz(n))
    ghz = Statevector.from_label("0" * n) / 2**0.5 + Statevector.from_label("1" * n) / 2**0.5
    got = "con la fase de GHZ" if qc is not None and Statevector(qc).equiv(ghz) else "con otra fase"
    assert got == "con la fase de GHZ", f"Con n = {n}, `programa_ghz` prepara el estado {got}."
