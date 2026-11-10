from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_sampler import Sampler
from qiskit_ibm_runtime.fake_provider import FakeManilaV2


def trotter(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
    return qc


def magnetizacion(conteos, n):
    return 0.0  # ✏️ cada bit 0 vale +1 y cada 1 vale -1; promedia sobre los n bits y los disparos


def magnetizacion_conteos(n, J, h, dt, pasos, disparos):
    backend = FakeManilaV2()
    qc = trotter(n, J, h, dt, pasos)
    qc.measure_all()
    isa = generate_preset_pass_manager(1, backend=backend, seed_transpiler=1).run(qc)
    sampler = Sampler(mode=backend)
    sampler.options.simulator.seed_simulator = 3
    conteos = sampler.run([isa], shots=disparos).result()[0].data.meas.get_counts()
    return magnetizacion(conteos, n)
