# Wrong: puts the Toffoli on the last three qubits.
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import CCXGate, HGate
from qiskit.converters import circuit_to_dag, dag_to_circuit


def envolver(circuito):
    dag = circuit_to_dag(circuito)
    dag.apply_operation_back(HGate(), qargs=[dag.qubits[0]])
    dag.apply_operation_front(CCXGate(), qargs=list(dag.qubits[-3:]))
    return dag_to_circuit(dag)


q = QuantumRegister(3, "q")
c = ClassicalRegister(3, "c")
circ = QuantumCircuit(q, c)
circ.h(q[0])
circ.cx(q[0], q[1])
circ.measure(q[0], c[0])
with circ.if_test((c, 2)):
    circ.rz(0.5, q[1])
print(dict(envolver(circ).count_ops()))
