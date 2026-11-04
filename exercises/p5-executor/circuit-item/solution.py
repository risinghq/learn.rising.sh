import numpy as np
from qiskit.circuit import Parameter, QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime import Executor
from qiskit_ibm_runtime.fake_provider import FakeManilaV2
from qiskit_ibm_runtime.quantum_program import QuantumProgram
from samplomatic import build
from samplomatic.transpiler import generate_boxing_pass_manager

backend = FakeManilaV2()
DISPAROS = 256
rng = np.random.default_rng(3)

# GHZ de 3 qubits con dos parámetros: ideal, solo salen 000 y 111.
circuito = QuantumCircuit(3)
circuito.h(0)
circuito.cx(0, 1)
circuito.cx(1, 2)
circuito.rz(Parameter("theta"), 0)
circuito.rz(Parameter("phi"), 1)
circuito.measure_all()

pm = generate_preset_pass_manager(backend=backend, optimization_level=0)

# ✏️ 10 configuraciones de los 2 parámetros: una matriz de números aleatorios
argumentos = rng.random((10, 2))

programa = QuantumProgram(shots=DISPAROS)
programa.append_circuit_item(pm.run(circuito), circuit_arguments=argumentos)
resultado = Executor(mode=backend).run(programa).result()
forma = resultado[0]["meas"].shape
print("forma de meas:", forma)

# ✏️ apuesta: ¿qué forma tiene `forma`? Los ejes de barrido, luego disparos y bits.
prediccion = (10, 256, 3)
