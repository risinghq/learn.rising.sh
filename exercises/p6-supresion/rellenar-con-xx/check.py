from qgcheck import inside, learner, visible

OPCIONES = [0, 2, 8]


def pulses(qc):
    return sum(1 for inst in qc.data if inst.operation.name == "x")


@inside
def added():
    return pulses(learner.con_xx) - pulses(learner.isa)


@inside
def added_by_xx():
    from qiskit.circuit.library import XGate

    return pulses(learner.con_dd([XGate(), XGate()])) - pulses(learner.isa)


@inside
def overlap_with_isa():
    import numpy as np
    from qiskit.quantum_info import Operator

    ua, ub = Operator(learner.isa).data, Operator(learner.con_xx).data
    return round(float(abs(np.trace(ua.conj().T @ ub)) / ua.shape[0]), 6)


@visible("`con_xx` añade pulsos X")
def test_pulses_added():
    n = added()
    assert n > 0, f"`con_xx` añade {n} pulsos X."


@visible("tu apuesta coincide con los pulsos añadidos")
def test_bet():
    n = added()
    assert learner.prediccion == min(OPCIONES, key=lambda o: abs(o - n)), (
        f"Apostaste {learner.prediccion}, pero `con_xx` añade {n} pulsos X."
    )


def test_same_operation():
    parecido = overlap_with_isa()
    assert parecido == 1.0, f"`con_xx` se parece a `isa` en {parecido}: no hace la misma operación."


def test_pulses_of_an_xx_sequence():
    n = added()
    assert n == added_by_xx(), f"`con_xx` añade {n} pulsos X, y no son los de una secuencia XX."
