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

pm_cajas = generate_preset_pass_manager(backend=backend, optimization_level=0)
pm_cajas.post_scheduling = generate_boxing_pass_manager(enable_gates=True, enable_measures=True)
plantilla, samplex = build(pm_cajas.run(circuito))

programa = QuantumProgram(shots=DISPAROS)
programa.append_samplex_item(
    plantilla,
    samplex=samplex,
    samplex_arguments={"parameter_values": rng.random((5, 2))},
    shape=(20, 5),
)
item = Executor(mode=backend).run(programa).result()[0]
forma_twirl = item["meas"].shape
print("forma de meas:", forma_twirl)
