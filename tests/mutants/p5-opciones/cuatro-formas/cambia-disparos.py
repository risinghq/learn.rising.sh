from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2
from qiskit_ibm_runtime.options_models import EstimatorOptions

backend = FakeManilaV2()

por_clase = Estimator(mode=backend, options=EstimatorOptions(default_precision=0.02))
por_dict = Estimator(mode=backend, options={"default_precision": 0.02})

por_atributo = Estimator(mode=backend)
por_atributo.options.default_precision = 0.02

por_update = Estimator(mode=backend)
por_update.options.update(default_precision=0.02, default_shots=1000)

sin_tocar = Estimator(mode=backend)

for nombre, e in [("clase", por_clase), ("dict", por_dict), ("atributo", por_atributo), ("update", por_update)]:
    print(nombre, e.options.default_precision)

prediccion = 1 / 64
