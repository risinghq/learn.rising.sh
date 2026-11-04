from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_sampler import Sampler
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

backend = FakeManilaV2()
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)


def fraccion_errores(conteos):
    """Fracción de disparos que no es todo ceros ni todo unos."""
    return 0.0   # ✏️ disparos que no son todo 0 ni todo 1, entre el total


def ghz_conteos(n):
    ghz = QuantumCircuit(n)
    ghz.h(0)
    for i in range(n - 1):
        ghz.cx(i, i + 1)
    ghz.measure_all()
    sampler = Sampler(mode=backend)
    sampler.options.default_shots = 4000
    sampler.options.simulator.seed_simulator = 11
    return sampler.run([pm.run(ghz)]).result()[0].data.meas.get_counts()


error_2 = fraccion_errores(ghz_conteos(2))
error_5 = fraccion_errores(ghz_conteos(5))
print(f"2 qubits: {error_2:.1%}, 5 qubits: {error_5:.1%}")
