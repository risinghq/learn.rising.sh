from qiskit import QuantumCircuit
from qiskit.circuit.library import DiagonalGate, grover_operator
from qiskit.quantum_info import Statevector, hellinger_fidelity
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer.noise import NoiseModel
from qiskit_aer.primitives import SamplerV2
from qiskit_ibm_runtime.fake_provider import FakePeekskill

backend = FakePeekskill()
ruido = NoiseModel.from_backend(backend, thermal_relaxation=False)
SHOTS = 4000


def grover3():
    qc = QuantumCircuit(3)
    qc.h([0, 1, 2])
    qc = qc.compose(grover_operator(DiagonalGate([1] * 7 + [-1])))
    return qc


def fidelidad(circuito, nivel):
    ideal = Statevector.from_instruction(circuito).probabilities_dict()
    medido = circuito.measure_all(inplace=False)
    # ✏️ transpila `medido` con ese nivel (seed_transpiler=0), simúlalo con ruido y compara con `ideal`
    return 0.0


print("nivel 3:", round(fidelidad(grover3(), 3), 3))
