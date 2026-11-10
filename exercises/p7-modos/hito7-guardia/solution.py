import math

from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez


def cadena(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for q in range(1, n - 1, 2):
            qc.rzz(2 * J * dt, q, q + 1)
        for q in range(0, n - 1, 2):
            qc.rzz(2 * J * dt, q, q + 1)
        for q in range(n):
            qc.rx(2 * h * dt, q)
    return qc


def guardia(n, J, h, dt, pasos, disparos, restante_s, activado):
    backend = FakeFez()
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1, seed_transpiler=1)
    agenda = generate_preset_pass_manager(target=backend.target, optimization_level=0, scheduling_method="alap")
    espera = backend.target["reset"][(0,)].duration + backend.default_rep_delay
    uso_s = 0
    for k in range(1, pasos + 1):
        duracion = agenda.run(pm.run(cadena(n, J, h, dt, k))).estimate_duration(backend.target, unit="s")
        uso_s += math.ceil(2 + (duracion + espera) * disparos)
    return activado and uso_s <= restante_s, uso_s
