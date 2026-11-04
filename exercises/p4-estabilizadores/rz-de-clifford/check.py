import numpy as np

from qgcheck import learner, visible


def rz_angles(circuit):
    return [inst.operation.params[0] for inst in circuit.data if inst.operation.name == "rz"]


@visible("el circuito corre con stabilizer y conserva su rz")
def test_runs():
    assert learner.conteos_rz is not None, "El simulador `stabilizer` sigue rechazando el circuito."
    assert rz_angles(learner.con_rz), "El circuito ya no tiene una `rz`: cambia solo el ángulo."


def test_angle_is_clifford():
    angle = learner.angulo
    steps = angle / (np.pi / 2)
    assert abs(steps - round(steps)) < 1e-9, f"Con angulo = {angle}, la rotación no es de Clifford."


def test_circuit_uses_the_angle():
    angles = rz_angles(learner.con_rz)
    assert angles == [learner.angulo], f"Con angulo = {learner.angulo}, `con_rz` rota los ángulos {angles}."


def test_distribution():
    strings = sorted(learner.conteos_rz or {})
    assert strings == ["00", "11"], f"`conteos_rz` tiene las cadenas {strings}."
