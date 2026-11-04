from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

backend = FakeManilaV2()


def crear_estimator(perfil):
    estimator = Estimator(mode=backend)
    estimator.options.default_shots = 4000
    if perfil == "crudo":
        pass   # ✏️ sin mitigación ni supresión
    else:
        pass   # ✏️ desacoplamiento XY4 y twirling de puertas y de mediciones
    return estimator


for perfil in ("crudo", "protegido"):
    opciones = crear_estimator(perfil).options
    print(perfil, opciones.resilience_level, opciones.dynamical_decoupling.enable, opciones.twirling.enable_gates)
