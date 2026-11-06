from qiskit.primitives import StatevectorEstimator
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeBelemV2


def patron(qc, obs, nivel):
    pm = generate_preset_pass_manager(optimization_level=nivel, backend=FakeBelemV2())
    isa = pm.run(qc)
    isa_obs = obs.apply_layout(isa.layout)
    resultado = StatevectorEstimator().run([(isa, isa_obs)]).result()
    return qc, float(resultado[0].data.evs)
