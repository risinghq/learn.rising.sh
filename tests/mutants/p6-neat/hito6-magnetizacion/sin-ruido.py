from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import SamplerV2


def trotter(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
    return qc


def magnetizacion_medida(n, J, h, dt, pasos, disparos):
    qc = trotter(n, J, h, dt, pasos)
    qc.measure_all()
    sampler = SamplerV2(options={"backend_options": {"seed_simulator": 3}})
    cuentas = sampler.run([(qc, None, disparos)]).result()[0].data.meas.get_counts()
    suma = 0
    for bits, veces in cuentas.items():
        for i in range(n):
            suma += veces * (1 - 2 * int(bits[n - 1 - i]))
    return suma / (n * disparos)
