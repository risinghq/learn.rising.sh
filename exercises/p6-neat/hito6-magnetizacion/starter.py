from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import SamplerV2
from qiskit_ibm_runtime.fake_provider import FakeManilaV2


def trotter(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
    return qc


def magnetizacion_medida(n, J, h, dt, pasos, disparos):
    backend = AerSimulator.from_backend(FakeManilaV2())
    pm = generate_preset_pass_manager(1, backend=backend, seed_transpiler=1)
    qc = trotter(n, J, h, dt, pasos)
    qc.measure_all()
    sampler = SamplerV2.from_backend(backend, options={"backend_options": {"seed_simulator": 3}})
    cuentas = sampler.run([(pm.run(qc), None, disparos)]).result()[0].data.meas.get_counts()
    return 0.0  # ✏️ ⟨M⟩ = (1/n) Σᵢ ⟨Zᵢ⟩ a partir de las cuentas; el qubit 0 es el bit de la derecha
