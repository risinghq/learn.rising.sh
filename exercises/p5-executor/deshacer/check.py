import numpy as np

from qgcheck import inside, learner, visible


@inside
def corrected_synthetic():
    meas = np.array([[[0, 1, 1], [1, 0, 0]]], dtype=bool)
    flips = np.array([[[1, 1, 0], [0, 0, 1]]], dtype=bool)
    return np.asarray(learner.deshacer({"meas": meas, "measurement_flips.meas": flips})).astype(int).tolist()


@inside
def corrected_real():
    item = learner.item
    bits = np.asarray(learner.deshacer(item))
    mismo_formato = bits.shape == item["meas"].shape
    es_el_xor = mismo_formato and bool(np.array_equal(bits, item["meas"] ^ item["measurement_flips.meas"]))
    return mismo_formato, es_el_xor, learner.fraccion_ghz(bits)


@visible("aplica el XOR de `measurement_flips.meas` a `meas`")
def test_xor():
    got = corrected_synthetic()
    assert got == [[[1, 0, 1], [1, 0, 1]]], f"Con unos bits de 3 qubits devuelve {got}."


def test_real_item_returns_to_ghz():
    mismo_formato, es_el_xor, fraccion = corrected_real()
    assert mismo_formato, "Con `item`, `deshacer` cambia la forma de los bits."
    assert es_el_xor, f"Con `item`, la fracción de disparos 000 o 111 es {round(fraccion, 2)}, pero los bits no son `meas` con los giros deshechos."
