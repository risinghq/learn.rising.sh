import itertools

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError
from qiskit_aer.primitives import SamplerV2


def trotter(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
    return qc


def lectura_ruidosa():
    ruido = NoiseModel()
    ruido.add_all_qubit_readout_error(ReadoutError([[0.95, 0.05], [0.15, 0.85]]))
    return ruido


def medir(circuitos, disparos):
    sampler = SamplerV2(options={"backend_options": {"noise_model": lectura_ruidosa(), "seed_simulator": 3}})
    return [r.data.meas.get_counts() for r in sampler.run([(c, None, disparos) for c in circuitos]).result()]


def con_volteo(qc, volteo):
    out = qc.copy()
    for i, b in enumerate(volteo):
        if b:
            out.x(i)
    out.measure_all()
    return out


def magnetizacion(cuentas, n, volteo):
    total = sum(cuentas.values())
    suma = 0
    for bits, veces in cuentas.items():
        for i in range(n):
            signo = 1 - 2 * int(bits[n - 1 - i])
            suma += veces * (-signo if volteo[i] else signo)
    return suma / (n * total)


def trex(n, J, h, dt, pasos, disparos):
    volteos = list(itertools.product([0, 1], repeat=n))
    base = trotter(n, J, h, dt, pasos)
    cuentas_tw = medir([con_volteo(base, v) for v in volteos], disparos)
    cuentas_cal = medir([con_volteo(QuantumCircuit(n), v) for v in volteos], disparos)
    m_tw = [magnetizacion(c, n, v) for c, v in zip(cuentas_tw, volteos)]
    m_cal = [magnetizacion(c, n, v) for c, v in zip(cuentas_cal, volteos)]
    return float(np.mean(m_tw) / np.mean(m_cal))
