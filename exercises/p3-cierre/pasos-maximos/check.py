import functools

from qgcheck import learner, visible

# DEPTHS records level-3 FakeFez depths for `trotter(n, pasos)`.
# The table avoids repeated transpilation within the 2.5 s CPU budget.
DEPTHS = {
    2: [14, 15, 15, 15, 15, 15, 15, 15, 15, 15],
    6: [45, 58, 74, 90, 106, 122, 138, 154, 170, 186],
}


def step(n):
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(n)
    for i in range(n - 1):
        qc.rzz(0.2, i, i + 1)
    for i in range(n):
        qc.rx(0.1, i)
    return qc


@functools.cache
def backend():
    from qiskit_ibm_runtime.fake_provider import FakeFez

    return FakeFez()


@functools.cache
def depths(n):
    """Transpiled depth (level 3, FakeFez, seed_transpiler=1) of 1 to 10 steps. Imports qiskit here so grading does not."""
    from qiskit import QuantumCircuit
    from qiskit.transpiler import generate_preset_pass_manager

    pm = generate_preset_pass_manager(3, backend=backend(), seed_transpiler=1)
    out = []
    for pasos in range(1, 11):
        qc = QuantumCircuit(n)
        for _ in range(pasos):
            qc.compose(step(n), inplace=True)
        out.append(pm.run(qc).depth())
    return out


def fits(n, budget):
    return max([p for p, d in enumerate(DEPTHS[n], start=1) if d <= budget], default=0)


@visible("con 6 espines y un presupuesto de 150 caben tantos pasos como indica la profundidad transpilada")
def test_budget():
    got = learner.pasos_max(6, 150)
    assert got == fits(6, 150), f"Con n = 6 y presupuesto = 150, `pasos_max` devuelve {got}; esperaba {fits(6, 150)}."


@visible("si ni un paso cabe, devuelve 0")
def test_nothing_fits():
    got = learner.pasos_max(1, 0)
    assert got == 0, f"Con n = 1 y presupuesto = 0, `pasos_max` devuelve {got}; ni un paso cabe."


def test_everything_fits():
    got = learner.pasos_max(1, 100000)
    assert got == 10, f"Con n = 1 y presupuesto = 100000, `pasos_max` devuelve {got}."


def test_equal_depth_fits():
    budget = DEPTHS[2][0]
    got = learner.pasos_max(2, budget)
    assert got == fits(2, budget), f"Con n = 2 y presupuesto = {budget}, `pasos_max` devuelve {got}."


if __name__ == "__main__":
    # Regenerate DEPTHS: PYTHONPATH=. uv run python exercises/p3-cierre/pasos-maximos/check.py
    print({n: depths(n) for n in DEPTHS})
