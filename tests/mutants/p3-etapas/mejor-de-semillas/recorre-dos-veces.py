# Wrong: iterates over `semillas` twice, so a generator arrives empty.
from qiskit.circuit.random import random_circuit
from qiskit.transpiler import CouplingMap, generate_preset_pass_manager

cuadricula = CouplingMap.from_grid(3, 3)
puertas_base = ["cx", "rz", "sx", "x"]
aleatorio = random_circuit(9, 6, max_operands=2, seed=7)


def transpilar(qc, semilla):
    pm = generate_preset_pass_manager(1, coupling_map=cuadricula, basis_gates=puertas_base, seed_transpiler=semilla)
    return pm.run(qc)


def mejor_de(qc, semillas):
    cuentas = [transpilar(qc, s).count_ops().get("cx", 0) for s in semillas]
    mejor = None
    for semilla in semillas:
        candidato = transpilar(qc, semilla)
        if mejor is None or candidato.count_ops().get("cx", 0) < mejor.count_ops().get("cx", 0):
            mejor = candidato
    return mejor


elegido = mejor_de(aleatorio, range(10))
print("cx del elegido:", None if elegido is None else elegido.count_ops().get("cx", 0))
