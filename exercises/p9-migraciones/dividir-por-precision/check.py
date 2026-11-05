from qgcheck import learner, visible

CASOS = {
    "A, B, C": [("A", 0.01), ("B", 0.05), ("C", 0.01)],
    "P, Q, R, S, T": [("P", 0.1), ("Q", 0.1), ("R", 0.5), ("S", 0.2), ("T", 0.5)],
}


@visible("A y C comparten precisión y forman un solo trabajo")
def test_shared_precision():
    got = learner.dividir(CASOS["A, B, C"])
    assert got == [["A", "C"], ["B"]], f"Con los PUBs {CASOS['A, B, C']}, `dividir` devuelve {got}."


def test_order_of_first_appearance():
    got = learner.dividir(CASOS["P, Q, R, S, T"])
    assert got == [["P", "Q"], ["R", "T"], ["S"]], (
        f"Con los PUBs {CASOS['P, Q, R, S, T']}, `dividir` devuelve {got}."
    )
