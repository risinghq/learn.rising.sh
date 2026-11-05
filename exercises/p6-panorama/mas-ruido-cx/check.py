import math

from qgcheck import inside, learner, visible


@inside
def remeasured(p_cx):
    return learner.fraccion_erronea(learner.medir(learner.bell, learner.modelo_ruido(p_cx, 0.02)))


@visible("entre el 12 % y el 50 % de los disparos es erróneo")
def test_fraction_in_range():
    fraccion = learner.frac_mas
    assert 0.12 < fraccion < 0.5, (
        f"Con `p_cx` = {learner.p_cx} el {fraccion:.1%} de los disparos es erróneo."
    )


def test_fraction_comes_from_p_cx():
    medida = remeasured(learner.p_cx)
    assert math.isclose(learner.frac_mas, medida, abs_tol=1e-9), (
        f"Con `p_cx` = {learner.p_cx}, `frac_mas` vale {learner.frac_mas} y no sale de medir con ese `p_cx`."
    )


def test_p_cx_is_a_probability_of_one_gate():
    assert 0 < learner.p_cx <= 0.5, (
        f"`p_cx` vale {learner.p_cx}: el error de una CX real no llega a tanto."
    )
