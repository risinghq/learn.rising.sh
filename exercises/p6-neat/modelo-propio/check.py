from qgcheck import inside, learner, visible


@inside
def own_model_again(p):
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    from qiskit_ibm_runtime.debug_tools import Neat

    modelo = NoiseModel()
    modelo.add_all_qubit_quantum_error(depolarizing_error(p, 2), ["cx"])
    ruidoso = Neat(learner.fake, noise_model=modelo).noisy_sim(learner.pubs_cliff, seed_simulator=1)
    return learner.diferencia_media(learner.ideal, ruidoso)


@visible("tu modelo da más diferencia que el del backend a 3 capas")
def test_more_pessimistic():
    propio, backend = learner.dif_propio[2], learner.dif_backend[2]
    assert propio > backend, (
        f"Con `p_cx` = {learner.p_cx} tu modelo da {propio:.1f} % a 3 capas y el del backend {backend:.1f} %."
    )


def test_difference_comes_from_p_cx():
    again = own_model_again(learner.p_cx)
    assert all(abs(a - b) < 1e-9 for a, b in zip(learner.dif_propio, again, strict=True)), (
        f"Con `p_cx` = {learner.p_cx}, `dif_propio` vale {[round(x, 2) for x in learner.dif_propio]} y al simular de nuevo sale {[round(x, 2) for x in again]}."
    )


def test_p_cx_is_one_gate_error():
    assert 0 < learner.p_cx <= 0.3, (
        f"`p_cx` vale {learner.p_cx}: el error de una CX real no llega a tanto."
    )
