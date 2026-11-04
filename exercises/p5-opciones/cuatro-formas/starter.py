from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2
from qiskit_ibm_runtime.options_models import EstimatorOptions

backend = FakeManilaV2()

por_clase = Estimator(mode=backend, options=EstimatorOptions(default_precision=0.02))
por_dict = Estimator(mode=backend, options={"default_precision": 0.02})

# ✏️ fija default_precision = 0.02 asignando un atributo de las opciones
por_atributo = Estimator(mode=backend)

# ✏️ fija default_precision = 0.02 con el método update de las opciones
por_update = Estimator(mode=backend)

sin_tocar = Estimator(mode=backend)

for nombre, e in [("clase", por_clase), ("dict", por_dict), ("atributo", por_atributo), ("update", por_update)]:
    print(nombre, e.options.default_precision)

# ✏️ apuesta: ¿cuánto vale default_precision en `sin_tocar`?
prediccion = None
