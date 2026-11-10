from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

from qgcheck import learner, visible


def trotter(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
    return qc


def uso(n, J, h, dt, pasos, disparos):
    """2 s fijos más, por circuito, (duración programada + reset + rep_delay) × disparos."""
    manila = FakeManilaV2()
    pm = generate_preset_pass_manager(backend=manila, optimization_level=1, seed_transpiler=1)
    programa = generate_preset_pass_manager(target=manila.target, optimization_level=0, scheduling_method="alap")
    espera = manila.target["reset"][(0,)].duration + manila.default_rep_delay
    total = 2.0
    for k in range(1, pasos + 1):
        isa = pm.run(trotter(n, J, h, dt, k))
        total += (programa.run(isa).estimate_duration(manila.target, unit="s") + espera) * disparos
    return total


def cerca(got, want):
    return isinstance(got, (int, float)) and abs(got - want) < 0.01 * want


@visible("4 espines, 6 circuitos de 4096 disparos en FakeManilaV2: unos 8.4 s de QPU")
def test_cuatro_espines():
    got = learner.estimar_uso(4, 1.0, 1.0, 0.25, 6, 4096)
    assert cerca(got, uso(4, 1.0, 1.0, 0.25, 6, 4096)), (
        f"`estimar_uso` devuelve {got!r} s y la estimación es {uso(4, 1.0, 1.0, 0.25, 6, 4096):.2f} s. "
        "Cada disparo dura el circuito más la espera del reset y de rep_delay."
    )


def test_tres_espines():
    got = learner.estimar_uso(3, 0.5, 0.8, 0.2, 3, 1000)
    assert cerca(got, uso(3, 0.5, 0.8, 0.2, 3, 1000)), (
        f"Con n = 3, J = 0.5, h = 0.8, dt = 0.2, pasos = 3 y disparos = 1000, `estimar_uso` devuelve {round(got, 3)!r} s."
    )
