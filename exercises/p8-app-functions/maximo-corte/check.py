from qgcheck import learner, visible


@visible("encuentra un corte de cuatro aristas")
def test_five_edges():
    aristas = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]
    got = learner.maximo_corte(aristas, 4)
    assert got[2] == 4 and len(got[1]) == 4, (
        f"Con aristas = {aristas}, `maximo_corte` devuelve {got}."
    )


def test_triangle():
    aristas = [(0, 1), (1, 2), (2, 0)]
    got = learner.maximo_corte(aristas, 3)
    assert got[2] == 2, f"Con aristas = {aristas}, `maximo_corte` devuelve {got}."
