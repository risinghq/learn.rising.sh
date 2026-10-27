# Wrong: adds the pair (0, 2) to the connectivity.
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Measure, Parameter
from qiskit.circuit.library import CZGate, RZGate, SXGate, XGate
from qiskit.providers import BackendV2, Options
from qiskit.transpiler import InstructionProperties, Target


class MiBackend(BackendV2):
    def __init__(self):
        super().__init__(name="mi_backend")
        self._target = Target("cadena de 3", num_qubits=3)
        self._target.add_instruction(
            RZGate(Parameter("t")),
            {(q,): InstructionProperties(error=0.0, duration=0.0) for q in range(3)},
        )
        for gate in (XGate(), SXGate(), Measure()):
            self._target.add_instruction(gate, {(q,): None for q in range(3)})
        self._target.add_instruction(
            CZGate(),
            {(0, 1): InstructionProperties(error=5e-3), (1, 2): InstructionProperties(error=5e-3), (0, 2): InstructionProperties(error=5e-3)},
        )

    @property
    def target(self):
        return self._target

    @property
    def max_circuits(self):
        return None

    @classmethod
    def _default_options(cls):
        return Options(shots=1024)

    def run(self, circuit, **kwargs):
        raise NotImplementedError


cx_lejana = QuantumCircuit(3)
cx_lejana.h(0)
cx_lejana.cx(0, 2)
print(sorted(transpile(cx_lejana, MiBackend(), seed_transpiler=1).count_ops()))
