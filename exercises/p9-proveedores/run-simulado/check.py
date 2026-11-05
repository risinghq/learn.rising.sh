from qgcheck import inside, learner, visible


@inside
def conteos(shots):
    from qiskit import QuantumCircuit
    from qiskit.primitives import BackendSamplerV2
    from qiskit.transpiler import generate_preset_pass_manager

    backend = learner.MiQPUSimulado()
    ghz = QuantumCircuit(3)
    ghz.h(0)
    ghz.cx(0, 1)
    ghz.cx(1, 2)
    ghz.measure_all()
    isa = generate_preset_pass_manager(1, backend=backend, seed_transpiler=1).run(ghz)
    sampler = BackendSamplerV2(backend=backend, options={"default_shots": shots})
    try:
        return sampler.run([isa]).result()[0].data.meas.get_counts()
    except Exception:
        return {}


@visible("el GHZ solo da 000 y 111")
def test_ghz_outcomes():
    got = sorted(conteos(500))
    assert got == ["000", "111"], f"Con 500 disparos, `run` produce los resultados {got}."


def test_shots_reach_the_simulator():
    got = sum(conteos(500).values())
    assert got == 500, f"Con 500 disparos, `run` produce {got} disparos."
