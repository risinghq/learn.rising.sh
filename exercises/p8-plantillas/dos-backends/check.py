from qgcheck import learner, visible


@visible("compara statevector y fake")
def test_three_steps():
    got = learner.comparar_backends(3)
    assert got[0] == 4 and abs(got[1] - 1) < 1e-9 and 0 < got[2] < 0.25, (
        f"Con t_steps = 3, `comparar_backends` devuelve {got}."
    )


def test_one_step():
    got = learner.comparar_backends(1)
    assert got[0] == 2 and abs(got[1] - 1) < 1e-9, (
        f"Con t_steps = 1, `comparar_backends` devuelve {got}."
    )
