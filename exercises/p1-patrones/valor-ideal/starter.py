from qiskit.primitives import StatevectorEstimator


def valor_ideal(isa, obs):
    isa_obs = obs.apply_layout(None, num_qubits=isa.num_qubits)
    resultado = StatevectorEstimator().run([(isa, isa_obs)]).result()
    return float(resultado[0].data.evs)
