from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez


def ejecutar(circuitos):
    backend = FakeFez()
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend, seed_transpiler=1)
    return [pm.run(circuito).depth() for circuito in circuitos]
