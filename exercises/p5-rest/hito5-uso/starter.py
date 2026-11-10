from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeManilaV2


def trotter(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
    return qc


def estimar_uso(n, J, h, dt, pasos, disparos):
    backend = FakeManilaV2()
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1, seed_transpiler=1)
    isas = [pm.run(trotter(n, J, h, dt, k)) for k in range(1, pasos + 1)]
    pm_t = generate_preset_pass_manager(target=backend.target, optimization_level=0, scheduling_method="alap")
    espera = backend.target["reset"][(0,)].duration + backend.default_rep_delay
    uso = 2.0
    for isa in isas:
        duracion = pm_t.run(isa).estimate_duration(backend.target, unit="s")
        uso += duracion * disparos
    return uso
