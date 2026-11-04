import functools

from qgcheck import learner, visible


@functools.cache
def correlaciones(n):
    return learner.correlaciones(n)


def buscadas(n):
    return ["I" * (n - 1 - i) + "Z" + "I" * (i - 1) + "Z" for i in range(1, n)]


@visible("n = 5: cuatro correlaciones cerca de 1")
def test_five_qubits():
    got = correlaciones(5)
    assert len(got) == 4, f"Con n = 5 devuelve {len(got)} correlaciones: {got}."
    bajas = {e: v for e, v in got.items() if not 0.6 < v < 1.05}
    assert not bajas, f"Con n = 5 devuelve {got}: se alejan de 1 {sorted(bajas)}."


def test_labels_put_z_on_qubit_0_and_i():
    for n in (5, 3):
        etiquetas = list(correlaciones(n))
        assert etiquetas == buscadas(n), f"Con n = {n} las etiquetas son {etiquetas}."

