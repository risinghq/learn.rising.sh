import math

import numpy as np

from qgcheck import inside, learner, visible


@inside
def model_fidelity():
    from qiskit.quantum_info import QubitSparsePauli

    return float(learner.modelo_aprendido.pauli_fidelity(QubitSparsePauli.from_label("ZZ")))


@visible("`aprender_fidelidad` recupera f = (1 − 0,03)²")
def test_fidelity():
    esperado = (1 - 0.03) ** 2
    got = learner.f_aprendida
    assert abs(got - esperado) < 1e-6, (
        f"`f_aprendida` vale {got:.5f}, con medidas = {np.round(learner.medidas, 4).tolist()}."
    )


@visible("el modelo con tu tasa reproduce esa fidelidad para ZZ")
def test_model_reproduces_it():
    got = model_fidelity()
    assert abs(got - learner.f_aprendida) < 1e-6, (
        f"Con `tasa` = {learner.tasa:.5f} la fidelidad de ZZ en el modelo es {got:.5f}, y `f_aprendida` vale {learner.f_aprendida:.5f}."
    )


def test_fit_uses_every_point():
    ds, valores = [1, 2, 3, 6], [0.95, 0.90, 0.84, 0.60]
    pendiente, _ = np.polyfit(ds, np.log(valores), 1)
    got = learner.aprender_fidelidad(ds, valores)
    assert math.isclose(got, float(np.exp(pendiente)), abs_tol=1e-6), (
        f"Con ds = {ds} y valores = {valores} devuelve f = {round(got, 5)}."
    )
