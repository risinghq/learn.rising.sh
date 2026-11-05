from qgcheck import inside, learner, visible


@inside
def duracion(duracion_1q, duracion_cz):
    from qiskit import QuantumCircuit
    from qiskit.transpiler import generate_preset_pass_manager

    target = learner.target_durable(duracion_1q, duracion_cz)
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 2)
    isa = generate_preset_pass_manager(1, target=target, seed_transpiler=1).run(qc)
    try:
        return f"{isa.estimate_duration(target):.3g} s"
    except Exception:
        return "no se puede estimar"


@inside
def errores():
    target = learner.target_durable(5e-8, 3e-7)
    x, cz = target["x"][(0,)].error, target["cz"][(0, 1)].error
    return f"{x} y {cz}"


@visible("el circuito dura 6e-07 s con 5e-8 y 3e-7")
def test_example():
    got = duracion(5e-8, 3e-7)
    assert got == "6e-07 s", f"Con duraciones 5e-8 y 3e-7, `target_durable` estima {got}."


def test_other_durations():
    got = duracion(1e-7, 5e-7)
    assert got == "1.1e-06 s", f"Con duraciones 1e-7 y 5e-7, `target_durable` estima {got}."


def test_keeps_errors():
    got = errores()
    assert got == "0.0001 y 0.01", f"Los errores de `target_durable` son {got}."
