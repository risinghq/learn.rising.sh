from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

backend = FakeManilaV2()


def crear_estimator(perfil):
    estimator = Estimator(mode=backend)
    estimator.options.default_shots = 4000
    if perfil == "crudo":
        estimator.options.resilience_level = 0
        estimator.options.dynamical_decoupling.enable = False
        estimator.options.twirling.enable_gates = False
        estimator.options.twirling.enable_measure = False
    else:
        estimator.options.dynamical_decoupling.enable = True
        estimator.options.dynamical_decoupling.sequence_type = "XY4"
        estimator.options.twirling.enable_gates = True
        estimator.options.twirling.enable_measure = True
    return estimator


for perfil in ("crudo", "protegido"):
    opciones = crear_estimator(perfil).options
    print(perfil, opciones.resilience_level, opciones.dynamical_decoupling.enable, opciones.twirling.enable_gates)
