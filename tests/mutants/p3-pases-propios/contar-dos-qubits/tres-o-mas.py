# Wrong: also counts the gates on three qubits or more.
from qiskit import QuantumCircuit
from qiskit.transpiler import PassManager
from qiskit.transpiler.basepasses import AnalysisPass


class ContarDosQubits(AnalysisPass):
    def run(self, dag):
        self.property_set["n2q"] = len([n for n in dag.op_nodes() if len(n.qargs) >= 2])


qc = QuantumCircuit(3)
qc.h(0)
qc.cx(0, 1)
qc.cz(1, 2)
qc.swap(0, 2)
pm = PassManager([ContarDosQubits()])
pm.run(qc)
print("n2q:", pm.property_set.get("n2q"))
