from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator

from qgcheck import inside, learner, visible

SHOTS = 20000


@inside
def wrong_readings(p01, p10, prepared):
    """Fraction of shots in which each qubit is read differently from how it was prepared."""
    qc = QuantumCircuit(len(prepared))
    for qubit, bit in enumerate(prepared):
        if bit:
            qc.x(qubit)
    qc.measure_all()
    sim = AerSimulator(noise_model=learner.modelo_lectura(p01, p10), seed_simulator=3)
    counts = sim.run(generate_preset_pass_manager(1, backend=sim).run(qc), shots=SHOTS).result().get_counts()
    return [
        sum(n for bits, n in counts.items() if int(bits[-1 - qubit]) != bit) / SHOTS
        for qubit, bit in enumerate(prepared)
    ]


@visible("con |1⟩ lees 0 el 10 % de las veces")
def test_reads_zero():
    got = wrong_readings(0.05, 0.10, [1])
    assert abs(got[0] - 0.10) < 0.01, f"Preparando |1⟩ lees 0 el {got[0]:.1%} de las veces."


@visible("con |0⟩ lees 1 el 5 % de las veces")
def test_reads_one():
    got = wrong_readings(0.05, 0.10, [0])
    assert abs(got[0] - 0.05) < 0.01, f"Preparando |0⟩ lees 1 el {got[0]:.1%} de las veces."


def test_asymmetric_two_qubits():
    got = wrong_readings(0.2, 0.0, [0, 1])
    assert abs(got[0] - 0.2) < 0.015 and got[1] == 0, (
        f"Con p01 = 0.2, p10 = 0.0 y preparados = '01' (un carácter por qubit, del primero al último), las lecturas erróneas por qubit son {got}.")


def test_three_qubits():
    got = wrong_readings(0.0, 0.3, [1, 1, 0])
    assert abs(got[0] - 0.3) < 0.015 and abs(got[1] - 0.3) < 0.015 and got[2] == 0, (
        f"Con p01 = 0.0, p10 = 0.3 y preparados = '110' (un carácter por qubit, del primero al último), las lecturas erróneas por qubit son {got}.")
