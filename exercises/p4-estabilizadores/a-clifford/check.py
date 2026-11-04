import numpy as np
from qiskit.circuit.library import efficient_su2
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator

from qgcheck import learner, visible

STEP = np.pi / 2


def rounded(params):
    return np.rint(np.asarray(params) / STEP) * STEP


@visible("redondea al múltiplo de π/2 más cercano")
def test_nearest():
    params = [0.1, 2.0, 4.0, 5.9]
    got = np.asarray(learner.a_clifford(params))
    assert np.allclose(got, rounded(params)), f"Con params = {params}, `a_clifford` devuelve {np.round(got, 3).tolist()}."


@visible("un efficient_su2 con esos ángulos corre con stabilizer")
def test_stabilizer_runs():
    base = efficient_su2(6)
    params = np.random.default_rng(3).uniform(0, 2 * np.pi, base.num_parameters)
    measured = base.copy()
    measured.measure_all()
    sim = AerSimulator(method="stabilizer", seed_simulator=3)
    pm = generate_preset_pass_manager(1, sim)
    got = np.asarray(learner.a_clifford(params))
    counts = sim.run(pm.run(measured.assign_parameters(got)), shots=64).result().get_counts()
    assert sum(counts.values()) == 64, f"`a_clifford` devuelve ángulos que `stabilizer` no acepta: {np.round(got[:4], 3).tolist()}…"


def test_negative_and_large():
    params = [-0.3, -2.0, 7.0, 10.0, -4.0]
    got = np.asarray(learner.a_clifford(params))
    assert np.allclose(got, rounded(params)), f"Con params = {params}, `a_clifford` devuelve {np.round(got, 3).tolist()}."


def test_keeps_the_shape():
    params = np.random.default_rng(5).uniform(-6, 6, 40)
    got = np.asarray(learner.a_clifford(params))
    assert got.shape == params.shape and np.allclose(got, rounded(params)), (
        f"Con 40 ángulos al azar, `a_clifford` devuelve algo de forma {got.shape}, con {int(np.sum(~np.isclose(got, rounded(params))))} ángulos mal redondeados.")
