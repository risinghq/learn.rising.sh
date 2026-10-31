"""Map of the course: parts and lessons, in order.

Each lesson in this plan must have its module (parte*.py) and the other way round.
The titles and descriptions are course text, so they are in Spanish.
"""

from typing import Any

# The exercises run and are graded in the learner's browser (docs/exercises.md).
RUNS = "browser"

PARTS: list[dict[str, Any]] = [
    dict(
        n=1,
        title="Parte I · Integrar el movimiento",
        desc="Tres sistemas, un mismo problema: cómo avanzar en el tiempo sin que la energía se escape. Euler y leapfrog en el oscilador, el péndulo sin aproximar y la órbita de un planeta.",
        lessons=[
            ("f1-euler-leapfrog", "Euler contra leapfrog: por qué la energía se desvía"),
            ("f1-pendulo", "El péndulo más allá de los ángulos pequeños"),
            ("f1-kepler", "Integrar un planeta: la órbita de Kepler"),
        ],
    ),
]
