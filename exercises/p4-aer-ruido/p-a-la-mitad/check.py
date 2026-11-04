from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

from qgcheck import learner, visible


def ghz6():
    qc = QuantumCircuit(6)
    qc.h(0)
    for k in range(5):
        qc.cx(k, k + 1)
    qc.measure_all()
    return qc


def fraction_correct(p, seed):
    noise = NoiseModel()
    noise.add_all_qubit_quantum_error(depolarizing_error(p, 2), ["cx"])
    sim = AerSimulator(noise_model=noise, seed_simulator=seed)
    counts = sim.run(generate_preset_pass_manager(1, backend=sim).run(ghz6()), shots=4000).result().get_counts()
    return (counts.get("0" * 6, 0) + counts.get("1" * 6, 0)) / 4000


@visible("la fracción correcta cae entre 0.55 y 0.65")
def test_half():
    fraction = learner.fraccion
    assert 0.55 <= fraction <= 0.65, f"La fracción es {fraction:.3f}. Sube `p` hasta que quede entre 0.55 y 0.65."


def test_other_seed():
    p = learner.p
    fraction = fraction_correct(p, 9)
    assert 0.5 <= fraction <= 0.7, f"Con p = {p} y otra semilla del simulador, la fracción correcta es {fraction:.3f}."
