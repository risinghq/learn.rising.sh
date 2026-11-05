from qgcheck import inside, learner, visible


@inside
def probabilidades():
    from qiskit.quantum_info import Statevector

    probs = Statevector(learner.bell()).probabilities_dict()
    return {str(k): round(float(v), 3) for k, v in probs.items()}


@inside
def misma_fase():
    import numpy as np
    from qiskit.quantum_info import Statevector

    objetivo = Statevector(np.array([1, 0, 0, 1]) / np.sqrt(2))
    return "con la fase de Bell" if Statevector(learner.bell()).equiv(objetivo) else "con otra fase"


@visible("la medición da 00 y 11 con la misma probabilidad")
def test_probabilities():
    got = probabilidades()
    assert got == {"00": 0.5, "11": 0.5}, f"`bell()` da las probabilidades {got}."


def test_same_state():
    got = misma_fase()
    assert got == "con la fase de Bell", f"`bell()` prepara el estado {got}."
