from qgcheck import learner, visible


@visible("amplitud pequeña, 0.1 rad: casi 2π")
def test_small_amplitude():
    got = learner.periodo(0.1)
    assert abs(got - 6.2871) < 0.01, f"Con theta0 = 0.1, `periodo` devuelve {got!r}."


@visible("amplitud de 1 rad: el péndulo ya es más lento que 2π")
def test_one_radian():
    got = learner.periodo(1.0)
    assert abs(got - 6.7000) < 0.01, f"Con theta0 = 1.0, `periodo` devuelve {got!r}."


def test_large_amplitude():
    got = learner.periodo(2.0)
    assert abs(got - 8.3498) < 0.01, f"Con theta0 = 2.0, `periodo` devuelve {got!r}."


def test_near_the_top():
    got = learner.periodo(3.0)
    assert abs(got - 16.1555) < 0.01, f"Con theta0 = 3.0, `periodo` devuelve {got!r}."
