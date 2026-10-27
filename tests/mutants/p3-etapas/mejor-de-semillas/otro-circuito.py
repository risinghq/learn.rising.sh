# Wrong: always transpiles the same circuit, not the one it receives.
from qiskit.circuit.random import random_circuit
from qiskit.transpiler import CouplingMap, generate_preset_pass_manager

cuadricula = CouplingMap.from_grid(3, 3)
puertas_base = ["cx", "rz", "sx", "x"]
aleatorio = random_circuit(9, 6, max_operands=2, seed=7)


def transpilar(qc, semilla):
    pm = generate_preset_pass_manager(1, coupling_map=cuadricula, basis_gates=puertas_base, seed_transpiler=semilla)
    return pm.run(qc)


def mejor_de(qc, semillas):
    mejor = None
    for semilla in semillas:
        candidato = transpilar(aleatorio, semilla)
        if mejor is None or candidato.count_ops().get("cx", 0) < mejor.count_ops().get("cx", 0):
            mejor = candidato
    return mejor


elegido = mejor_de(aleatorio, range(10))
print("cx del elegido:", None if elegido is None else elegido.count_ops().get("cx", 0))
