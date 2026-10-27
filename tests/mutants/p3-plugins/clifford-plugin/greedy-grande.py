# Wrong: also synthesizes with 4 qubits, with another method.
from qiskit import QuantumCircuit
from qiskit.quantum_info import Clifford, random_clifford
from qiskit.synthesis import synth_clifford_bm, synth_clifford_greedy
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import HighLevelSynthesis
from qiskit.transpiler.passes.synthesis.high_level_synthesis import HLSConfig
from qiskit.transpiler.passes.synthesis.plugin import HighLevelSynthesisPlugin


class MiClifford(HighLevelSynthesisPlugin):
    def run(self, high_level_object, coupling_map=None, target=None, qubits=None, **options):
        if high_level_object.num_qubits <= 4:
            return (synth_clifford_bm if high_level_object.num_qubits <= 3 else synth_clifford_greedy)(high_level_object)
        return None


def sintetiza(cl, metodos):
    qc = QuantumCircuit(cl.num_qubits)
    qc.append(cl, range(cl.num_qubits))
    return PassManager([HighLevelSynthesis(hls_config=HLSConfig(clifford=metodos))]).run(qc)


for n in (3, 4):
    print(n, "qubits:", dict(sintetiza(random_clifford(n, seed=1), [(MiClifford(), {})]).count_ops()))
