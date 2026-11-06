from qiskit.primitives import StatevectorEstimator


def valor_ideal(isa, obs):
    isa_obs = obs[0].apply_layout(isa.layout)
    resultado = StatevectorEstimator().run([(isa, isa_obs)]).result()
    return float(resultado[0].data.evs)
