from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error


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
    return (c.get("0" * 6, 0) + c.get("1" * 6, 0)) / sum(c.values())


p = 0.0   # ✏️ probabilidad despolarizante de cada CX

ruido_p = NoiseModel()
ruido_p.add_all_qubit_quantum_error(depolarizing_error(p, 2), ["cx"])
fraccion = correctos(conteos(ghz(6), ruido_p))
print(f"p = {p} → correctos {fraccion:.3f} · estimación (1-p)^5 = {(1 - p) ** 5:.3f}")
