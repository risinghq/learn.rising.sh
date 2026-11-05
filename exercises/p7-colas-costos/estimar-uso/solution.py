import math

from qiskit.transpiler import generate_preset_pass_manager


def estimar_uso(backend, qc, ejecuciones):
    pm = generate_preset_pass_manager(
        target=backend.target, optimization_level=0, scheduling_method="alap"
    )
    por_ejecucion = pm.run(qc).estimate_duration(backend.target, unit="s")
    por_ejecucion += backend.target["reset"][(0,)].duration
    por_ejecucion += backend.default_rep_delay
    return math.ceil(2 + por_ejecucion * ejecuciones)
