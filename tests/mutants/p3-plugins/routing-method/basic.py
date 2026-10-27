# Wrong: keeps the basic method.
from qiskit.circuit.random import random_circuit
from qiskit.transpiler import CouplingMap, generate_preset_pass_manager

cuadricula = CouplingMap.from_grid(3, 3)
aleatorio = random_circuit(9, 6, max_operands=2, seed=3)
metodo = "basic"
pm_routing = generate_preset_pass_manager(
    2, coupling_map=cuadricula, basis_gates=["cx", "rz", "sx", "x"],
    routing_method=metodo, seed_transpiler=0)
cx_routing = pm_routing.run(aleatorio).count_ops().get("cx", 0)
print(metodo, "→", cx_routing, "CNOT")
