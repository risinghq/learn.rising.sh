from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

fake = FakeManilaV2()
estimator = Estimator(fake, options={"resilience_level": 0})
opciones = estimator.options

# ✏️ activa TREX (measure_mitigation), ZNE (zne_mitigation) y zne.noise_factors = (1, 3, 5)

r = opciones.resilience
print("nivel:", opciones.resilience_level)
print("TREX:", r.measure_mitigation, "· ZNE:", r.zne_mitigation, "· factores:", r.zne.noise_factors)
