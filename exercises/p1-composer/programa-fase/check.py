from qgcheck import learner, visible


def amplitudes(texto):
    from qiskit import qasm2
    from qiskit.quantum_info import Statevector

    try:
        qc = qasm2.loads(texto)
    except Exception:
        return None
    return [complex(round(a.real, 6), round(a.imag, 6)) for a in Statevector(qc).data]


def mostrar(valores):
    if valores is None:
        return "un programa que Qiskit no lee"
    return [f"{v.real:g}{v.imag:+g}i" for v in valores]


@visible("con angulo = pi/2 la amplitud de 11 es i/2")
def test_quarter_turn():
    from math import pi

    angulo = pi / 2
    got = amplitudes(learner.programa_fase(angulo))
    assert got is not None and got[3] == 0.5j, (
        f"Con angulo = {angulo:.4f}, `programa_fase` da las amplitudes {mostrar(got)}."
    )


def test_other_angle():
    from cmath import exp
    from math import pi

    angulo = pi / 3
    got = amplitudes(learner.programa_fase(angulo))
    esperado = 0.5 * exp(1j * angulo)
    assert got is not None and abs(got[3] - esperado) < 1e-5, (
        f"Con angulo = {angulo:.4f}, `programa_fase` da las amplitudes {mostrar(got)}."
    )


def test_only_eleven_changes():
    from math import pi

    angulo = pi / 2
    got = amplitudes(learner.programa_fase(angulo))
    assert got is not None and got[:3] == [0.5, 0.5, 0.5], (
        f"Con angulo = {angulo:.4f}, `programa_fase` da las amplitudes {mostrar(got)}."
    )


def test_no_phase():
    angulo = 0.0
    got = amplitudes(learner.programa_fase(angulo))
    assert got is not None and got == [0.5, 0.5, 0.5, 0.5], (
        f"Con angulo = {angulo}, `programa_fase` da las amplitudes {mostrar(got)}."
    )
