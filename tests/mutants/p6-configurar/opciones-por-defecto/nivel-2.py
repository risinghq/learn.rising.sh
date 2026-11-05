from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

fake = FakeManilaV2()
estimator = Estimator(fake, options={"resilience_level": 2})

# ✏️ lee el nivel de resiliencia que trae el Estimator sin pedir nada
nivel_por_defecto = estimator.options.resilience_level
print("resilience_level:", nivel_por_defecto)
print("measure_mitigation:", estimator.options.resilience.measure_mitigation)
print("zne_mitigation:", estimator.options.resilience.zne_mitigation)

# ✏️ apuesta antes de mirar las líneas de arriba: ¿qué nivel es: 0, 1 o 2?
prediccion = 2
