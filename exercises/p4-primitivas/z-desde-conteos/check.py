from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

from qgcheck import learner, visible


def z_expected(counts, k):
    total = sum(counts.values())
    return sum(n * (1 - 2 * int(bits[-1 - k])) for bits, n in counts.items()) / total


@visible("el qubit 0 es el carácter de la derecha")
def test_order():
    counts = {"10": 30, "00": 10}
    for k in (0, 1):
        got = learner.z_desde_conteos(counts, k)
        assert abs(got - z_expected(counts, k)) < 1e-9, f"Con conteos = {counts} y k = {k}, `z_desde_conteos` devuelve {got!r}."


@visible("coincide con Estimator: cos(0.8) en el qubit 0 y 1 en el qubit 1")
def test_matches_estimator():
    qc = QuantumCircuit(3)
    qc.ry(0.8, 0)
    qc.measure_all()
    counts = StatevectorSampler(seed=5).run([qc], shots=20000).result()[0].data.meas.get_counts()
    z0, z1 = learner.z_desde_conteos(counts, 0), learner.z_desde_conteos(counts, 1)
    assert abs(z0 - 0.6967) < 0.03, f"Con los conteos de Ry(0.8) en el qubit 0, `z_desde_conteos(conteos, 0)` devuelve {z0:.3f}."
    assert abs(z1 - 1) < 1e-9, f"Con los conteos de Ry(0.8) en el qubit 0, `z_desde_conteos(conteos, 1)` devuelve {z1:.3f}."


def test_every_qubit():
    counts = {"011": 2, "100": 6, "110": 2, "000": 10}
    for k in (0, 1, 2):
        got = learner.z_desde_conteos(counts, k)
        assert abs(got - z_expected(counts, k)) < 1e-9, f"Con conteos = {counts} y k = {k}, `z_desde_conteos` devuelve {got!r}."


def test_average_not_sum():
    counts = {"0": 750, "1": 250}
    got = learner.z_desde_conteos(counts, 0)
    assert abs(got - z_expected(counts, 0)) < 1e-9, f"Con conteos = {counts} y k = 0, `z_desde_conteos` devuelve {got!r}."
