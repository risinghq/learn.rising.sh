from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_sampler import Sampler
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

backend = FakeManilaV2()
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)

bell = QuantumCircuit(2, 2)
bell.h(0)
bell.cx(0, 1)
bell.measure([0, 1], [0, 1])
isa = pm.run(bell)

sampler = Sampler(mode=backend)
sampler.options.default_shots = 300
sampler.options.simulator.seed_simulator = 5
registro = sampler.run([isa]).result()[0].data.c

# Lo que devolvería el servicio: un hexadecimal por disparo.
muestras = [hex(int(bits, 2)) for bits in registro.get_bitstrings()]


def decodificar(muestras, n_bits):
    conteos = {}
    for h in muestras:
        bits = format(int(h, 16), "02b")
        conteos[bits] = conteos.get(bits, 0) + 1
    return conteos


esperados = registro.get_counts()
decodificados = decodificar(muestras, 2)
print(muestras[:8], "…")
print(dict(sorted(decodificados.items())))
