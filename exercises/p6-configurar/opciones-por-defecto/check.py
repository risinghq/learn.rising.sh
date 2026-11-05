from qgcheck import inside, learner, visible


@inside
def level_of_estimator():
    return learner.estimator.options.resilience_level


@inside
def level_of_a_new_one():
    from qiskit_ibm_runtime.executor_estimator import Estimator

    return Estimator(learner.fake).options.resilience_level


@visible("`nivel_por_defecto` es el nivel de `estimator`")
def test_level_read():
    nivel = level_of_estimator()
    assert learner.nivel_por_defecto == nivel, (
        f"`nivel_por_defecto` vale {learner.nivel_por_defecto!r}."
    )


@visible("tu apuesta coincide con el nivel por defecto")
def test_bet():
    nivel = level_of_estimator()
    assert learner.prediccion == nivel, (
        f"Apostaste {learner.prediccion}, pero `estimator` trae el nivel {nivel}."
    )


def test_estimator_was_created_without_options():
    nuevo = level_of_a_new_one()
    assert level_of_estimator() == nuevo, (
        f"`estimator` tiene el nivel {level_of_estimator()}, no el que trae un Estimator recién creado."
    )
