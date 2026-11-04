from qiskit.primitives import StatevectorSampler

from qgcheck import inside, learner, visible


class CountingSampler:
    """A StatevectorSampler that records how many times `run` is called and the PUBs it receives."""

    def __init__(self, seed):
        self.inner = StatevectorSampler(seed=seed)
        self.calls = 0
        self.shots = []

    def run(self, pubs, *, shots=None):
        self.calls += 1
        self.shots += [pub[2] if isinstance(pub, tuple) and len(pub) > 2 else None for pub in pubs]
        return self.inner.run(pubs, shots=shots)


@inside
def run_with(disparos, seed):
    sampler = CountingSampler(seed)
    errores = learner.errores_por_disparos(sampler, disparos)
    return {"errores": [float(e) for e in errores], "llamadas": sampler.calls, "disparos": sampler.shots}


@visible("cuatro errores con 100, 1 000, 10 000 y 100 000 disparos")
def test_four_errors():
    shots = [100, 1000, 10_000, 100_000]
    got = run_with(shots, 11)["errores"]
    assert len(got) == 4 and got[-1] < 0.005, f"Con disparos = {shots}, `errores_por_disparos` devuelve {[round(e, 4) for e in got]}."


def test_one_call():
    shots = [50, 500, 5000]
    got = run_with(shots, 4)
    assert got["llamadas"] == 1, f"Con disparos = {shots}, `errores_por_disparos` llama a `run` {got['llamadas']} veces."


def test_shots_of_each_pub():
    shots = [50, 500, 5000]
    got = run_with(shots, 4)["disparos"]
    assert got == shots, f"Con disparos = {shots}, los PUBs piden los disparos {got}."


def test_absolute_errors():
    shots = [40_000, 160_000]
    got = run_with(shots, 6)["errores"]
    assert len(got) == 2 and all(0 <= e < 0.012 for e in got), f"Con disparos = {shots}, `errores_por_disparos` devuelve {[round(e, 4) for e in got]}."
