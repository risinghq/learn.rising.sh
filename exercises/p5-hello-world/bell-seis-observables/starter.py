from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

backend = FakeManilaV2()
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)

bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)

etiquetas = ["IZ", "IX", "ZI", "XI", "ZZ", "XX"]
isa_bell = pm.run(bell)
mapeados = [SparsePauliOp(e).apply_layout(isa_bell.layout) for e in etiquetas]

estimator = Estimator(mode=backend)
estimator.options.default_shots = 5000
estimator.options.simulator.seed_simulator = 7

# ✏️ ejecuta un PUB con isa_bell y los seis observables mapeados, y guarda en `valores`
# un diccionario etiqueta → valor esperado, redondeado a 2 decimales
valores = {}
print(valores)

# ✏️ apuesta: ¿qué etiquetas valdrán casi 1? Escríbelas en la lista.
prediccion = []
