from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeBelemV2


def a_isa(qc):
    backend = FakeBelemV2()
    pm = generate_preset_pass_manager(
        optimization_level=1, basis_gates=list(backend.operation_names)
    )
    return pm.run(qc)
