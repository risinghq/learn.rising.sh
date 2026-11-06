from qiskit.primitives import StatevectorEstimator


def valor_ideal(isa, obs):
    fisicos = isa.layout.initial_index_layout(filter_ancillas=True)
    isa_obs = obs.apply_layout(list(reversed(fisicos)), num_qubits=isa.num_qubits)
    resultado = StatevectorEstimator().run([(isa, isa_obs)]).result()
    return float(resultado[0].data.evs)
