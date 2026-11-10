from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
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
    disparos = sum(conteos.values())
    suma = sum(cuenta * sum(1 if bit == "0" else -1 for bit in cadena) for cadena, cuenta in conteos.items())
    return suma / (n * disparos)


def magnetizacion_conteos(n, J, h, dt, pasos, disparos):
    backend = FakeManilaV2()
    qc = trotter(n, J, h, dt, pasos)
    qc.measure_all()
    conteos = StatevectorSampler(seed=3).run([qc], shots=disparos).result()[0].data.meas.get_counts()
    return magnetizacion(conteos, n)
