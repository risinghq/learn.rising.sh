from concurrent.futures import ThreadPoolExecutor

from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez

_EXECUTOR = ThreadPoolExecutor(max_workers=4)


def distribute_task(target):
    def decorador(funcion):
        return lambda *args: _EXECUTOR.submit(funcion, *args)

    return decorador


def get(refs):
    return [ref.result() for ref in refs]


def profundidades(circuitos):
    backend = FakeFez()

    @distribute_task(target={"cpu": 1})
    def transpilar(circuito):
        pm = generate_preset_pass_manager(optimization_level=1, backend=backend, seed_transpiler=1)
        return pm.run(circuito).depth()

    refs = [transpilar(circuito) for circuito in circuitos]
    return get(refs)
