from qgcheck import learner, visible


@visible("95 %, 85 % y 50 %")
def test_guide_examples():
    for dif, esperado in [(95, []), (85, ["PEA"]), (50, ["PEA", "ZNE"])]:
        got = learner.sugerencia(dif)
        assert got == esperado, f"Con dif = {dif} devuelve {got}."


def test_edges_are_strict():
    for dif in (90, 80):
        got = learner.sugerencia(dif)
        assert got == (["PEA"] if dif == 80 else []), f"Con dif = {dif} devuelve {got}."


def test_other_values():
    for dif in (0, 79.9, 89.9, 100):
        got = learner.sugerencia(dif)
        assert got == (["PEA", "ZNE"] if dif < 80 else ["PEA"] if dif < 90 else []), (
            f"Con dif = {dif} devuelve {got}."
        )
