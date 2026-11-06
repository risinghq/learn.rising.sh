from qiskit.primitives import StatevectorEstimator
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeBelemV2


def patron(qc, obs, nivel):
    backend = FakeBelemV2()
    pm = generate_preset_pass_manager(
        optimization_level=nivel, basis_gates=list(backend.operation_names)
    )
    isa = pm.run(qc)
    resultado = StatevectorEstimator().run([(isa, obs)]).result()
    return isa, float(resultado[0].data.evs)
