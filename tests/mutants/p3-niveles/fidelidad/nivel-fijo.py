# Wrong: always transpiles at level 3.
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
    isa = generate_preset_pass_manager(3, backend=backend, seed_transpiler=0).run(medido)
    sampler = SamplerV2(seed=7, options={"backend_options": {"noise_model": ruido}})
    cuentas = sampler.run([isa], shots=SHOTS).result()[0].data.meas.get_counts()
    return hellinger_fidelity({k: v / SHOTS for k, v in cuentas.items()}, ideal)


print("nivel 3:", round(fidelidad(grover3(), 3), 3))
