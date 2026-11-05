from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.executor_sampler import Sampler
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

fake = FakeManilaV2()


def preparar(primitiva, tecnicas):
    """Devuelve un Estimator ("estimator") o un Sampler ("sampler") con las técnicas pedidas."""
    p = Estimator(fake) if primitiva == "estimator" else Sampler(fake)
    if "dd" in tecnicas:
        p.options.dynamical_decoupling.enable = True
    # ✏️ twirling de puertas ("twirling"), TREX ("trex") y ZNE ("zne"); un Sampler no admite las dos últimas
    return p


try:
    preparar("sampler", {"trex"})
except ValueError as error:
    print("el Sampler rechaza TREX:", error)
