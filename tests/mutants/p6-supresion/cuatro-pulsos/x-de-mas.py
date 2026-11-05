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


base = pulsos_x(con_dd([XGate(), XGate()])) - pulsos_x(isa)

secuencia = [XGate(), XGate(), XGate(), XGate()]
con_secuencia = con_dd(secuencia)
con_secuencia.x(0)
pulsos_secuencia = pulsos_x(con_secuencia) - pulsos_x(isa)
print(f"con XX: {base} pulsos · con tu secuencia: {pulsos_secuencia}")
print("misma operación:", Operator(isa).equiv(Operator(con_secuencia)))
