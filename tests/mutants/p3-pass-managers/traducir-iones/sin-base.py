# Wrong: consolidates the blocks without the ion gates.
from qiskit import QuantumCircuit
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import Collect2qBlocks, ConsolidateBlocks, UnitarySynthesis

puertas_iones = ["rx", "ry", "rxx"]
traducir = PassManager([
    Collect2qBlocks(),
    ConsolidateBlocks(),
    UnitarySynthesis(puertas_iones),
])

circuito_hcx = QuantumCircuit(2)
circuito_hcx.h(0)
circuito_hcx.cx(0, 1)
circuito_hcx.cx(1, 0)
print(sorted(traducir.run(circuito_hcx).count_ops()))
