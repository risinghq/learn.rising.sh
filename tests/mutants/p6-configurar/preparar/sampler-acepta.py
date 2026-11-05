from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.executor_sampler import Sampler
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

fake = FakeManilaV2()


def preparar(primitiva, tecnicas):
    """Devuelve un Estimator ("estimator") o un Sampler ("sampler") con las técnicas pedidas."""
    p = Estimator(fake) if primitiva == "estimator" else Sampler(fake)
    if "dd" in tecnicas:
        p.options.dynamical_decoupling.enable = True
    if "twirling" in tecnicas:
        p.options.twirling.enable_gates = True
    if primitiva == "estimator" and "trex" in tecnicas:
        p.options.resilience.measure_mitigation = True
    if primitiva == "estimator" and "zne" in tecnicas:
        p.options.resilience.zne_mitigation = True
    return p


try:
    preparar("sampler", {"trex"})
except ValueError as error:
    print("el Sampler rechaza TREX:", error)
