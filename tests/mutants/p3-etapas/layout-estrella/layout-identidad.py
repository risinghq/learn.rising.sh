# Wrong: uses the identity layout, which needs SWAP.
from qiskit import QuantumCircuit
from qiskit.transpiler import CouplingMap, generate_preset_pass_manager

# Physical qubit 1 has three neighbors (0, 2 and 3); qubit 0 has only one.
chip = CouplingMap([[0, 1], [1, 2], [1, 3], [3, 4]])
chip.make_symmetric()

estrella = QuantumCircuit(4)
estrella.cx(0, 1)
estrella.cx(0, 2)
estrella.cx(0, 3)

# element i is the physical qubit where virtual qubit i goes
layout_inicial = [0, 1, 2, 3]

pm = generate_preset_pass_manager(0, coupling_map=chip, initial_layout=layout_inicial, seed_transpiler=1)
print("swaps:", pm.run(estrella).count_ops().get("swap", 0))
