from concurrent.futures import ThreadPoolExecutor

_EXECUTOR = ThreadPoolExecutor(max_workers=4)


def distribute_task(target):
    def decorador(funcion):
        return lambda *args: _EXECUTOR.submit(funcion, *args)

    return decorador


def get(refs):
    return [ref.result() for ref in refs]


def profundidades(circuitos):
    @distribute_task(target={"cpu": 1})
    def transpilar(circuito):
        return None

    refs = []
    return get(refs)
