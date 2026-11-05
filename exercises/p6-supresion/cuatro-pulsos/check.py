from qgcheck import inside, learner, visible


@inside
def overlap_with_isa():
    import numpy as np
    from qiskit.quantum_info import Operator

    ua, ub = Operator(learner.isa).data, Operator(learner.con_secuencia).data
    return round(float(abs(np.trace(ua.conj().T @ ub)) / ua.shape[0]), 6)


@inside
def pulses_added():
    return learner.pulsos_x(learner.con_secuencia) - learner.pulsos_x(learner.isa)


@visible("el doble de pulsos que con XX")
def test_double():
    n = learner.pulsos_secuencia
    assert n == 2 * learner.base, f"`pulsos_secuencia` vale {n}, y con XX se añaden {learner.base}."


def test_value_is_what_the_circuit_has():
    n = pulses_added()
    assert learner.pulsos_secuencia == n, (
        f"`pulsos_secuencia` vale {learner.pulsos_secuencia} pero `con_secuencia` añade {n} pulsos X."
    )


def test_same_operation():
    parecido = overlap_with_isa()
    assert parecido == 1.0, (
        f"Con tu `secuencia`, `con_secuencia` se parece a `isa` en {parecido}: no hace la misma operación."
    )
