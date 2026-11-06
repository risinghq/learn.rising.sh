from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeBelemV2


def a_isa(qc):
    return qc
