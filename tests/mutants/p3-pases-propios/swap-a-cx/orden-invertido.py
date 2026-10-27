# Wrong: does not replace the swaps whose first qubit is greater than the second.
from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister
from qiskit.circuit.library import CXGate, SwapGate
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler import PassManager
from qiskit.transpiler.basepasses import TransformationPass


class SwapACx(TransformationPass):
    def run(self, dag):
        for nodo in dag.op_nodes():
            if nodo.name != "swap" or dag.find_bit(nodo.qargs[0]).index > dag.find_bit(nodo.qargs[1]).index:
                continue
            mini = DAGCircuit()
            reg = QuantumRegister(2)
            mini.add_qreg(reg)
            for a, b in ((0, 1), (1, 0), (0, 1)):
                mini.apply_operation_back(CXGate(), [reg[a], reg[b]])
            dag.substitute_node_with_dag(nodo, mini)
        return dag


qc = QuantumCircuit(3)
qc.h(0)
qc.swap(0, 1)
qc.cx(1, 2)
qc.swap(1, 2)
print(dict(PassManager([SwapACx()]).run(qc).count_ops()))
