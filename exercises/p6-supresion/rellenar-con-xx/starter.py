from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import XGate
from qiskit.quantum_info import Operator
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDynamicalDecoupling
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

fake = FakeManilaV2()
logico = QuantumCircuit(3)
logico.h(0)
for _ in range(3):
    logico.cx(0, 1)
logico.cx(1, 2)
logico.h(2)
isa = transpile(logico, fake, optimization_level=0, initial_layout=[0, 1, 2], seed_transpiler=1)


def con_dd(secuencia):
    """Programa el circuito y rellena los huecos de espera con la secuencia."""
    pm = PassManager(
        [
            ALAPScheduleAnalysis(target=fake.target),
            PadDynamicalDecoupling(target=fake.target, dd_sequence=secuencia),
        ]
    )
    return pm.run(isa)


def pulsos_x(qc):
    return sum(1 for inst in qc.data if inst.operation.name == "x")


con_xx = isa  # ✏️ rellena los huecos con una secuencia XX
print("pulsos X añadidos:", pulsos_x(con_xx) - pulsos_x(isa))
print("misma operación:", Operator(isa).equiv(Operator(con_xx)))

# ✏️ apuesta antes de mirar las líneas de arriba: ¿cuántos pulsos X se añaden: 0, 2 u 8?
prediccion = None
