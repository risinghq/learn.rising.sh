from qiskit.circuit import Measure, Parameter
from qiskit.circuit.library import CZGate, RZGate, SXGate, XGate
from qiskit.providers import BackendV2, Options
from qiskit.providers.basic_provider import BasicSimulator
from qiskit.transpiler import InstructionProperties, Target


class MiQPU(BackendV2):
    def __init__(self):
        super().__init__(name="mi_qpu")
        self._target = Target(num_qubits=3)
        theta = Parameter("θ")
        for puerta in (RZGate(theta), SXGate(), XGate(), Measure()):
            self._target.add_instruction(
                puerta, {(q,): InstructionProperties(error=1e-4) for q in range(3)}
            )
        self._target.add_instruction(
            CZGate(),
            {(0, 1): InstructionProperties(error=1e-2), (1, 2): InstructionProperties(error=1e-2)},
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


class MiQPUSimulado(MiQPU):
    def run(self, run_input, **options):
        return BasicSimulator().run(run_input)
