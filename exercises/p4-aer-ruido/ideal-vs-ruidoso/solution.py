from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

n = 6


def ghz(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    for k in range(n - 1):
        qc.cx(k, k + 1)
    qc.measure_all()
    return qc


def conteos(qc, ruido, shots=4000):
    sim = AerSimulator(noise_model=ruido, seed_simulator=5)
    isa = generate_preset_pass_manager(1, backend=sim).run(qc)
    return sim.run(isa, shots=shots).result().get_counts()


def correctos(c):
    return (c.get("0" * n, 0) + c.get("1" * n, 0)) / sum(c.values())


ruido_cx = NoiseModel()
ruido_cx.add_all_qubit_quantum_error(depolarizing_error(0.02, 2), ["cx"])

ideal = correctos(conteos(ghz(n), None))
ruidoso = correctos(conteos(ghz(n), ruido_cx))

prediccion = 0.93
print(f"correctos: ideal {ideal:.3f} · con ruido {ruidoso:.3f}")
