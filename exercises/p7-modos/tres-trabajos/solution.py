from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime import Batch
from qiskit_ibm_runtime.executor_sampler import Sampler
from qiskit_ibm_runtime.fake_provider import FakeBelemV2


def trabajos(n_trabajos):
    backend = FakeBelemV2()
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    bell = QuantumCircuit(2)
    bell.h(0)
    bell.cx(0, 1)
    bell.measure_all()
    isa = pm.run(bell)
    with Batch(backend=backend, max_time="25m") as lote:
        sampler = Sampler(mode=lote)
        jobs = [sampler.run([isa]) for _ in range(n_trabajos)]
        return [sum(job.result()[0].data.meas.get_counts().values()) for job in jobs]
