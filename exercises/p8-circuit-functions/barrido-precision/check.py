from qgcheck import learner, visible


@visible("cuadruplica los disparos")
def test_precision_sweep():
    precisiones = (0.1, 0.05, 0.025)
    got = learner.dispersiones(precisiones)
    disparos = [got[str(eps)][0] for eps in precisiones]
    assert disparos == [100, 400, 1600] and 1.7 < got["0.1"][1] / got["0.05"][1] < 2.3, (
        f"Con precisiones = {precisiones}, `dispersiones` devuelve {got}."
    )


def test_two_precisions():
    precisiones = (0.1, 0.05)
    got = learner.dispersiones(precisiones)
    assert got["0.05"][0] == 4 * got["0.1"][0], (
        f"Con precisiones = {precisiones}, `dispersiones` devuelve {got}."
    )
