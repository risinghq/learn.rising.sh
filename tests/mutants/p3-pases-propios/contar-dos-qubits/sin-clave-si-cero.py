# Wrong: does not write the key when there are no two-qubit gates.
from qiskit import QuantumCircuit
from qiskit.transpiler import PassManager
from qiskit.transpiler.basepasses import AnalysisPass


class ContarDosQubits(AnalysisPass):
    def run(self, dag):
        if dag.two_qubit_ops():
            self.property_set["n2q"] = len(dag.two_qubit_ops())


qc = QuantumCircuit(3)
qc.h(0)
qc.cx(0, 1)
qc.cz(1, 2)
qc.swap(0, 2)
pm = PassManager([ContarDosQubits()])
pm.run(qc)
print("n2q:", pm.property_set.get("n2q"))
