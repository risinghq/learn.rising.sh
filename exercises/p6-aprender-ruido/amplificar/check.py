import math

from qgcheck import inside, learner, visible


@inside
def amplified(factor):
    original = [float(r) for r in learner.modelo.rates]
    nuevo = learner.amplificar(learner.modelo, factor)
    return original, [float(r) for r in nuevo.rates], float(nuevo.inverse().gamma())


@visible("con factor 3 las tasas se triplican y γ pasa a γ³")
def test_factor_three():
    original, tasas, gamma = amplified(3)
    assert all(math.isclose(t, 3 * o) for t, o in zip(tasas, original, strict=True)), (
        f"Con factor = 3 las tasas quedan {tasas}."
    )
    assert math.isclose(gamma, math.exp(2 * sum(original)) ** 3), (
        f"Con factor = 3, γ vale {gamma:.5f}."
    )


def test_other_factors():
    for factor in (1, 2, 0.5):
        original, tasas, _ = amplified(factor)
        assert all(math.isclose(t, factor * o) for t, o in zip(tasas, original, strict=True)), (
            f"Con factor = {factor} las tasas quedan {tasas}."
        )


def test_original_model_is_not_changed():
    original, *_ = amplified(3)
    again, *_ = amplified(3)
    assert original == again, f"Tras amplificar con factor = 3, las tasas de `modelo` son {again}."
