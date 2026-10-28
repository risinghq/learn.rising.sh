"""Parte I · Integrar el movimiento: oscilador, péndulo y órbita de Kepler.

Las curvas de las gráficas se calculan aquí, al generar la lección, con los mismos métodos
que enseña la lección.
"""

import math

from lib import (
    A,
    Block,
    Code,
    Exercise,
    L,
    M,
    Out,
    Plot,
    T,
    beat,
    choice,
    lesson,
    numeric,
    predict,
    reflect,
)

Point = tuple[float, float]


def resumen(items: list[str]) -> tuple[list[Block], list[Block]]:
    """Escena y acciones de un paso de resumen con una lista que aparece por partes."""
    marks = ("r1", "r2", "r3", "r4")
    return [L(items, id="r", stagger=True)], [
        A("item", "r", at=m, i=k) for k, m in enumerate(marks[: len(items)])
    ]


def line(seq: list[Point], keep: int = 240) -> list[list[float]]:
    """A polyline with at most `keep` points, rounded to what the screen can tell apart."""
    stride = max(1, len(seq) // keep)
    picked = [*seq[::stride], seq[-1]]
    return [[round(x, 4), round(y, 4)] for x, y in picked]


def oscilador(metodo: str, dt: float, pasos: int) -> list[Point]:
    """(x, v) del oscilador a = -x desde x = 1, v = 0."""
    x, v = 1.0, 0.0
    out = [(x, v)]
    for _ in range(pasos):
        if metodo == "euler":
            x, v = x + dt * v, v - dt * x
        else:
            v -= 0.5 * dt * x
            x += dt * v
            v -= 0.5 * dt * x
        out.append((x, v))
    return out


def energia_oscilador(estados: list[Point], dt: float) -> list[Point]:
    return [(k * dt, 0.5 * (x * x + v * v)) for k, (x, v) in enumerate(estados)]


def pendulo(theta0: float, dt: float, hasta: float) -> list[Point]:
    """(t, theta) del péndulo g = L = 1 soltado en reposo, con leapfrog."""
    theta, omega = theta0, 0.0
    out = [(0.0, theta)]
    for k in range(1, round(hasta / dt) + 1):
        omega -= 0.5 * dt * math.sin(theta)
        theta += dt * omega
        omega -= 0.5 * dt * math.sin(theta)
        out.append((k * dt, theta))
    return out


def periodo(theta0: float, dt: float = 0.002) -> float:
    theta, omega, t = theta0, 0.0, 0.0
    while True:
        omega -= 0.5 * dt * math.sin(theta)
        nuevo = theta + dt * omega
        omega -= 0.5 * dt * math.sin(nuevo)
        t += dt
        if nuevo <= 0:
            return 4 * (t - dt + dt * theta / (theta - nuevo))
        theta = nuevo


def aceleracion(x: float, y: float) -> Point:
    r3 = (x * x + y * y) ** 1.5
    return -x / r3, -y / r3


def kepler(metodo: str, dt: float, pasos: int) -> list[tuple[float, float, float, float]]:
    """(x, y, vx, vy) de un planeta con GM = 1 lanzado desde (1, 0) con velocidad (0, 0.8)."""
    x, y, vx, vy = 1.0, 0.0, 0.0, 0.8
    out = [(x, y, vx, vy)]
    ax, ay = aceleracion(x, y)
    for _ in range(pasos):
        if metodo == "euler":
            x, y, vx, vy = x + dt * vx, y + dt * vy, vx + dt * ax, vy + dt * ay
            ax, ay = aceleracion(x, y)
        else:
            vx += 0.5 * dt * ax
            vy += 0.5 * dt * ay
            x += dt * vx
            y += dt * vy
            ax, ay = aceleracion(x, y)
            vx += 0.5 * dt * ax
            vy += 0.5 * dt * ay
        out.append((x, y, vx, vy))
    return out


def momento(estados: list[tuple[float, float, float, float]], dt: float) -> list[Point]:
    return [(k * dt, x * vy - y * vx) for k, (x, y, vx, vy) in enumerate(estados)]


EULER = oscilador("euler", 0.1, 200)
SALTO = oscilador("leapfrog", 0.1, 200)

s_cierre1, a_cierre1 = resumen(
    [
        "Euler multiplica la energía por $1+\\Delta t^2$ en cada paso: crece sin parar",
        "leapfrog alterna medio paso de velocidad, paso de posición y medio paso de velocidad",
        "la energía de leapfrog oscila un poco, pero no se escapa",
        "un método se elige por lo que conserva, no solo por su precisión en un paso",
    ]
)
euler_leapfrog = lesson(
    "f1-euler-leapfrog",
    "Euler contra leapfrog: por qué la energía se desvía",
    "El oscilador armónico integrado con dos métodos de coste casi igual: Euler gana energía en cada paso y leapfrog la conserva. Se ve en una cuenta de una línea.",
    [
        "predecir qué hace la energía en un método de integración antes de ejecutarlo",
        "demostrar que Euler multiplica la energía del oscilador por $1+\\Delta t^2$ en cada paso",
        "escribir un paso de leapfrog y comprobar que la energía queda acotada",
    ],
    [
        beat(
            "oscilador",
            ("", "El oscilador armónico"),
            """Empecemos por el sistema más simple de la física: una masa colgada de un muelle.
             [[ec]]Con la masa y la constante del muelle iguales a uno, la aceleración es menos la posición.
             [[sol]]La solución exacta es un coseno, y la velocidad es menos un seno.
             [[en]]Lo importante es lo que no cambia. La energía, un medio de la velocidad al cuadrado más un medio de la posición al cuadrado, vale siempre lo mismo. Si soltamos la masa desde la posición uno, en reposo, la energía es un medio.""",
            [
                M(r"\ddot x=-x", id="ec", size=54, hidden=True),
                M(r"x(t)=\cos t,\qquad v(t)=-\sin t", id="sol", size=46, hidden=True),
                M(
                    r"E=\tfrac12 v^2+\tfrac12 x^2=\tfrac12",
                    id="en",
                    size=54,
                    hidden=True,
                ),
            ],
            [A("show", "ec", at="ec"), A("show", "sol", at="sol"), A("show", "en", at="en")],
        ),
        beat(
            "euler",
            ("", "El método de Euler"),
            """Un ordenador no resuelve la ecuación: avanza a pasos pequeños.
             [[idea]]El método de Euler es el más directo. En cada paso de tiempo, la posición avanza con la velocidad que tiene ahora, y la velocidad cambia con la aceleración que tiene ahora.
             [[codigo]]En Python son dos asignaciones en una sola línea, que usan a la vez los valores viejos de la posición y de la velocidad.""",
            [
                M(
                    r"x_{n+1}=x_n+v_n\,\Delta t\qquad v_{n+1}=v_n-x_n\,\Delta t",
                    id="reglas",
                    size=46,
                ),
                Code(
                    """dt = 0.1
x, v = 1.0, 0.0
for paso in range(200):
    x, v = x + dt * v, v - dt * x
energia = 0.5 * (x**2 + v**2)""",
                    id="c",
                    hidden=True,
                ),
            ],
            [A("show", "c", at="codigo"), A("hl", "c", at="codigo", lines=[4])],
        ),
        beat(
            "apuesta",
            ("", "Apuesta"),
            """Antes de ejecutarlo, apuesta. [[apuesta]]Con un paso de tiempo de cero coma uno y doscientos pasos, el reloj llega al tiempo veinte, unas tres oscilaciones. La energía empezó en un medio. ¿Cómo estará al final?""",
            [
                Code(
                    """dt = 0.1
x, v = 1.0, 0.0
for paso in range(200):
    x, v = x + dt * v, v - dt * x
energia = 0.5 * (x**2 + v**2)""",
                ),
                T("La energía empieza en 0,5", "subtitle"),
            ],
            ask=predict(
                "Tras 200 pasos, ¿cuánto vale la energía?",
                [
                    "Sigue en 0,5: un método que avanza en el tiempo no crea energía",
                    "Un poco menos de 0,5",
                    "Entre 0,5 y 1",
                    "Más de 1,5",
                ],
                "Anotado. Ejecutémoslo.",
            ),
        ),
        beat(
            "resultado",
            ("", "El resultado"),
            """Ejecutamos. [[out]]La energía final es tres coma sesenta y seis. Siete veces la que había al principio. [[mal]]No hay ninguna fuerza que empuje la masa: la energía la fabrica el propio método.""",
            [
                Code(
                    """dt = 0.1
x, v = 1.0, 0.0
for paso in range(200):
    x, v = x + dt * v, v - dt * x
energia = 0.5 * (x**2 + v**2)
print(f"E = {energia:.3f}")""",
                    id="c",
                ),
                Out("E = 3.658", id="o", hidden=True, check=True),
            ],
            [A("show", "o", at="out")],
        ),
        beat(
            "crece",
            ("", "La energía crece"),
            """Esta es la energía en función del tiempo. [[euler]]Con Euler sube en cada oscilación, y no se detiene. [[ref]]La línea discontinua es lo que debería hacer: quedarse en un medio.""",
            [
                Plot(
                    id="p",
                    w=1000,
                    h=440,
                    xr=[0, 20],
                    yr=[0, 4],
                    xticks=[0, 5, 10, 15, 20],
                    yticks=[0, 1, 2, 3, 4],
                    xlabel="t",
                    ylabel="energía",
                    curves=[
                        dict(
                            pts=line(energia_oscilador(EULER, 0.1)),
                            color="red",
                            hidden=True,
                            label="Euler",
                            lx=16,
                            ly=3.3,
                        ),
                        dict(
                            pts=[[0, 0.5], [20, 0.5]],
                            color="muted",
                            width=3,
                            dash="10 8",
                            hidden=True,
                            label="exacta",
                            lx=16.5,
                            ly=0.8,
                        ),
                    ],
                ),
            ],
            [A("curve", "p", at="euler", i=0, dur=2.2), A("curve", "p", at="ref", i=1, dur=0.8)],
        ),
        beat(
            "espiral",
            ("", "En el plano posición-velocidad"),
            """Veámoslo de otra forma. [[fase]]En el plano de la posición y la velocidad, el movimiento correcto es un círculo, porque la energía fija el radio. [[espiral]]Euler dibuja una espiral que se abre: el radio crece un poco en cada paso.""",
            [
                Plot(
                    id="p",
                    w=520,
                    h=520,
                    pw=420,
                    ph=420,
                    xr=[-3, 3],
                    yr=[-3, 3],
                    xlabel="x",
                    ylabel="v",
                    curves=[
                        dict(
                            pts=line(
                                [
                                    (math.cos(t / 40 * math.tau), -math.sin(t / 40 * math.tau))
                                    for t in range(41)
                                ]
                            ),
                            color="muted",
                            width=3,
                            dash="10 8",
                            hidden=True,
                        ),
                        dict(
                            pts=line([(x, v) for x, v in EULER]),
                            color="red",
                            hidden=True,
                        ),
                    ],
                ),
            ],
            [A("curve", "p", at="fase", i=0, dur=1.2), A("curve", "p", at="espiral", i=1, dur=2.5)],
        ),
        beat(
            "porque",
            ("", "Por qué crece"),
            """La causa cabe en una cuenta. [[uno]]Tras un paso de Euler, la energía es un medio de la nueva posición al cuadrado más la nueva velocidad al cuadrado. [[dos]]Al desarrollar, los términos cruzados se cancelan, y queda la energía anterior multiplicada por uno más el paso de tiempo al cuadrado. [[tres]]Es un factor fijo, mayor que uno, en cada paso. No es un error de redondeo ni una mala elección del paso: es el método.""",
            [
                M(
                    r"E_{n+1}=\tfrac12\big[(x+v\,\Delta t)^2+(v-x\,\Delta t)^2\big]",
                    id="m1",
                    size=40,
                    hidden=True,
                ),
                M(
                    r"E_{n+1}=\tfrac12(x^2+v^2)\,(1+\Delta t^2)=E_n\,(1+\Delta t^2)",
                    id="m2",
                    size=40,
                    hidden=True,
                ),
                M(r"E_n=E_0\,(1+\Delta t^2)^n", id="m3", size=54, hidden=True),
            ],
            [A("show", "m1", at="uno"), A("show", "m2", at="dos"), A("show", "m3", at="tres")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Usa la fórmula para calcular cuánto crece la energía.""",
            [M(r"E_n=E_0\,(1+\Delta t^2)^n", size=54)],
            ask=numeric(
                "Con $\\Delta t=0{,}1$, ¿por qué número se multiplica la energía tras 100 pasos? Redondea a dos decimales.",
                2.7,
                "$(1+0{,}1^2)^{100}=1{,}01^{100}\\approx 2{,}70$. Tras 200 pasos son $7{,}32$: la energía $0{,}5\\cdot 7{,}32=3{,}66$ que acabamos de ver.",
                tol=0.01,
                hint="El factor por paso es $1+\\Delta t^2=1{,}01$. Elévalo a la potencia 100.",
            ),
        ),
        beat(
            "leapfrog",
            ("", "Leapfrog"),
            """Hay una alternativa que cuesta casi lo mismo. Se llama leapfrog, salto de rana, y divide el paso en tres.
             [[kick]]Medio paso que cambia la velocidad con la aceleración de ahora. [[drift]]Un paso entero que mueve la posición con esa velocidad. [[kick2]]Y otro medio paso de velocidad, con la aceleración de la nueva posición.
             [[costo]]En un problema real, esa última aceleración es la del principio del paso siguiente, así que se calcula una sola vez por paso, igual que en Euler.""",
            [
                L(
                    [
                        "**kick**: $v \\leftarrow v + \\tfrac12\\,a(x)\\,\\Delta t$",
                        "**drift**: $x \\leftarrow x + v\\,\\Delta t$",
                        "**kick**: $v \\leftarrow v + \\tfrac12\\,a(x)\\,\\Delta t$",
                    ],
                    id="l",
                    stagger=True,
                    size=34,
                ),
            ],
            [
                A("item", "l", at="kick", i=0),
                A("item", "l", at="drift", i=1),
                A("item", "l", at="kick2", i=2),
            ],
        ),
        beat(
            "salto",
            ("", "Leapfrog en Python"),
            """El código. [[bucle]]Tres líneas dentro del bucle, en el orden del salto de rana. Con la aceleración igual a menos la posición, cada medio paso es una resta. [[out]]Ahora la energía no crece: oscila muy poco, entre cero coma cuatro nueve nueve y cero coma cinco.""",
            [
                Code(
                    """dt = 0.1
x, v = 1.0, 0.0
energias = []
for paso in range(200):
    v -= 0.5 * dt * x
    x += dt * v
    v -= 0.5 * dt * x
    energias.append(0.5 * (x**2 + v**2))
print(f"E mínima = {min(energias):.4f}")
print(f"E máxima = {max(energias):.4f}")""",
                    id="c",
                ),
                Out("E mínima = 0.4988\nE máxima = 0.5000", id="o", hidden=True, check=True),
            ],
            [A("hl", "c", at="bucle", lines=[5, 6, 7]), A("show", "o", at="out")],
        ),
        beat(
            "comparacion",
            ("", "Los dos métodos"),
            """Los dos métodos en el mismo plano. [[salto]]Leapfrog recorre un círculo, o casi: una elipse muy poco achatada que se cierra sobre sí misma. [[euler]]Euler se aleja del círculo y no vuelve.""",
            [
                Plot(
                    id="p",
                    w=520,
                    h=520,
                    pw=420,
                    ph=420,
                    xr=[-3, 3],
                    yr=[-3, 3],
                    xlabel="x",
                    ylabel="v",
                    curves=[
                        dict(pts=line(SALTO), color="teal", hidden=True),
                        dict(pts=line(EULER), color="red", hidden=True),
                    ],
                ),
            ],
            [A("curve", "p", at="salto", i=0, dur=1.5), A("curve", "p", at="euler", i=1, dur=2.5)],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Una última pregunta sobre Euler.""",
            [M(r"E_n=E_0\,(1+\Delta t^2)^n", size=54)],
            ask=choice(
                "Reduces el paso de tiempo a la mitad, pero sigues hasta el mismo tiempo final. ¿Qué pasa con la energía de Euler?",
                [
                    "Deja de crecer: con un paso menor el método es exacto",
                    "Crece más despacio, pero no se detiene",
                    "Crece igual: el factor por paso no depende del paso de tiempo",
                    "Decrece, porque ahora hay el doble de pasos",
                ],
                1,
                "Con $n=t/\\Delta t$ pasos, $(1+\\Delta t^2)^{t/\\Delta t}\\approx e^{\\Delta t\\,t}$: la mitad de paso reduce el exponente a la mitad, y la energía a tiempo 20 pasa de $3{,}7$ a $1{,}4$. Pero sigue creciendo.",
                wrong=[
                    "El factor $1+\\Delta t^2$ sigue siendo mayor que 1, así que crece.",
                    None,
                    "Sí depende: $\\Delta t^2$ es menor.",
                    "Hay más pasos, pero cada uno multiplica por un factor más cercano a 1; el efecto neto sigue siendo un aumento.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Escribe tú el paso de leapfrog para el oscilador, y comprueba que la energía no se escapa aunque des diez mil pasos.""",
            [
                Exercise(
                    "f1-euler-leapfrog/leapfrog",
                    "Escribe `leapfrog(x, v, dt, pasos)`: avanza el oscilador de aceleración `-x` con `pasos` pasos de leapfrog (medio paso de velocidad, paso de posición y otro medio paso de velocidad) y devuelve la tupla `(x, v)` final. Con `pasos = 0` devuelve el estado de partida.",
                    level=3,
                    needs="python",
                    id="e1",
                    hidden=True,
                    hints=[
                        "Leapfrog alterna medio paso de velocidad, un paso de posición y otro medio paso de velocidad.",
                        "Las tres líneas van dentro de un bucle que se repite `pasos` veces; la aceleración es `-x`, con la `x` de ese momento.",
                        "Cada medio paso de velocidad tiene la forma `v -= 0.5 * dt * ...`; el paso de posición, `x += dt * ...`.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma.""",
            [T("Un método no solo se equivoca: también se equivoca en una dirección.", "subtitle")],
            ask=reflect(
                "Euler y leapfrog cuestan casi lo mismo por paso. ¿Qué mirarías para decidir cuál usar en una simulación que dura millones de pasos?",
                "Leapfrog también cambia la energía un poco, pero no se acumula. ¿Qué diferencia hay entre un error que oscila y uno que se acumula?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Euler multiplica la energía por uno más el paso de tiempo al cuadrado en cada paso: crece sin parar. [[r2]]Leapfrog alterna medio paso de velocidad, un paso de posición y otro medio paso de velocidad. [[r3]]Su energía oscila un poco, pero no se escapa. [[r4]]Un método se elige por lo que conserva, no solo por su precisión en un paso.""",
            s_cierre1,
            a_cierre1,
        ),
    ],
    practice=[
        "Repite el experimento de Euler con un paso de tiempo de 0,01 y comprueba que la energía final concuerda con $0{,}5\\,e^{0{,}01\\cdot t}$.",
        "Cambia el oscilador por uno con aceleración $-4x$ y busca la energía conservada.",
    ],
)

AMPLITUDES = (0.2, 1.5, 2.9)
TRAYECTORIAS = [pendulo(th, 0.02, 20) for th in AMPLITUDES]
CURVA_T = [(round(th / 20, 3), periodo(th / 20 + 0.0)) for th in range(1, 63)]
T_90 = periodo(math.pi / 2)

s_cierre2, a_cierre2 = resumen(
    [
        "para ángulos pequeños $\\sin\\theta\\approx\\theta$ y el periodo es $2\\pi$, sea cual sea la amplitud",
        "fuera de ese límite, el periodo crece con la amplitud: un 18 % a 90°",
        "cerca de 180° el periodo se dispara",
        "con leapfrog se mide cruzando la vertical e interpolando entre dos pasos",
    ]
)
pendulo_les = lesson(
    "f1-pendulo",
    "El péndulo más allá de los ángulos pequeños",
    "El periodo de un péndulo depende de la amplitud. Se integra la ecuación sin aproximar el seno y se mide el periodo en función del ángulo inicial.",
    [
        "explicar por qué el periodo no depende de la amplitud solo para ángulos pequeños",
        "medir el periodo de una simulación cruzando la vertical e interpolando",
        "describir cómo crece el periodo con la amplitud, hasta dispararse cerca de 180°",
    ],
    [
        beat(
            "ecuacion",
            ("", "La ecuación del péndulo"),
            """Un péndulo de longitud uno, en un campo de gravedad uno, cumple que la aceleración angular es menos el seno del ángulo.
             [[ec]]Esa es toda la física. [[peq]]Para ángulos pequeños, el seno de theta es casi theta, y la ecuación es la del oscilador de la lección anterior: el periodo vale dos pi, sea cual sea la amplitud.
             [[grande]]Pero el seno se queda por debajo de theta en cuanto el ángulo crece. La fuerza que devuelve el péndulo es más débil de lo que supone la aproximación.""",
            [
                M(r"\ddot\theta=-\sin\theta", id="ec", size=54, hidden=True),
                M(
                    r"\sin\theta\approx\theta\ \Rightarrow\ T=2\pi",
                    id="peq",
                    size=46,
                    hidden=True,
                ),
                Plot(
                    id="p",
                    w=640,
                    h=300,
                    pw=480,
                    ph=260,
                    xr=[0, 3.3],
                    yr=[0, 3.3],
                    xticks=[[1.5708, "π/2"], [3.1416, "π"]],
                    xlabel="θ",
                    curves=[
                        dict(
                            expr="x",
                            color="muted",
                            dash="10 8",
                            width=3,
                            hidden=True,
                            label="θ",
                            lx=2.9,
                            ly=3.0,
                        ),
                        dict(
                            expr="sin(x)", color="blue", hidden=True, label="sen θ", lx=2.6, ly=0.7
                        ),
                    ],
                ),
            ],
            [
                A("show", "ec", at="ec"),
                A("show", "peq", at="peq"),
                A("curve", "p", at="peq", i=0, dur=0.8),
                A("curve", "p", at="grande", i=1, dur=1.2),
            ],
        ),
        beat(
            "apuesta",
            ("", "Apuesta"),
            """Apuesta antes de medir. [[apuesta]]Sueltas el péndulo en reposo desde noventa grados, un cuarto de vuelta, en vez de desde cinco. ¿Cómo será su periodo comparado con dos pi?""",
            [T("T ≟ 2π", "title")],
            ask=predict(
                "Soltado desde 90°, el periodo del péndulo es…",
                [
                    "Igual a $2\\pi$: no depende de la amplitud",
                    "Algo menor que $2\\pi$",
                    "Algo mayor: menos de un 50 % más",
                    "Mucho mayor: más del doble",
                ],
                "Anotado. Primero miremos el movimiento.",
            ),
        ),
        beat(
            "trayectorias",
            ("", "Tres amplitudes"),
            """Integramos la ecuación con leapfrog, la misma receta de la lección anterior, y dibujamos el ángulo en función del tiempo.
             [[a]]Con unos once grados, el vaivén es un coseno perfecto de periodo dos pi. [[b]]Con unos ochenta y seis, los picos ya se ensanchan y el vaivén se retrasa. [[c]]Con unos ciento sesenta y seis, el péndulo se queda mucho tiempo casi arriba, y cada oscilación dura bastante más.""",
            [
                Plot(
                    id="p",
                    w=1000,
                    h=440,
                    xr=[0, 20],
                    yr=[-3.3, 3.3],
                    xticks=[0, 5, 10, 15, 20],
                    yticks=[-3, 0, 3],
                    xlabel="t",
                    ylabel="θ",
                    curves=[
                        dict(pts=line(TRAYECTORIAS[0]), color="teal", hidden=True),
                        dict(pts=line(TRAYECTORIAS[1]), color="gold", hidden=True),
                        dict(pts=line(TRAYECTORIAS[2]), color="red", hidden=True),
                    ],
                ),
            ],
            [
                A("curve", "p", at="a", i=0, dur=1.5),
                A("curve", "p", at="b", i=1, dur=1.5),
                A("curve", "p", at="c", i=2, dur=1.5),
            ],
        ),
        beat(
            "medir",
            ("", "Medir el periodo"),
            """Para medir el periodo, soltamos el péndulo y anotamos cuándo cruza la vertical. [[cuarto]]Ese instante es un cuarto de periodo. [[interp]]El paso casi nunca cae justo en el cruce, así que interpolamos entre los dos puntos que lo rodean. [[tabla]]Con cinco grados sale dos pi. Con noventa, dieciocho por ciento más. Con ciento setenta y cinco, casi tres veces más.""",
            [
                Code(
                    """import math

def periodo(theta0, dt=0.001):
    theta, omega, t = theta0, 0.0, 0.0
    while True:
        omega -= 0.5 * dt * math.sin(theta)
        nuevo = theta + dt * omega
        omega -= 0.5 * dt * math.sin(nuevo)
        t += dt
        if nuevo <= 0:
            cruce = t - dt + dt * theta / (theta - nuevo)
            return 4 * cruce
        theta = nuevo

for grados in (5, 30, 90, 150, 175):
    T = periodo(math.radians(grados))
    print(f"{grados:>3}°  T = {T:.4f}  T/2π = {T / (2 * math.pi):.4f}")""",
                    id="c",
                ),
                Out(
                    "  5°  T = 6.2862  T/2π = 1.0005\n 30°  T = 6.3926  T/2π = 1.0174\n 90°  T = 7.4163  T/2π = 1.1803\n150°  T = 11.0723  T/2π = 1.7622\n175°  T = 18.0809  T/2π = 2.8777",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="cuarto", lines=[9, 10, 11, 12]),
                A("hl", "c", at="interp", lines=[11]),
                A("show", "o", at="tabla"),
            ],
        ),
        beat(
            "curva",
            ("", "El periodo contra la amplitud"),
            """Repetimos la medida para muchas amplitudes. [[linea]]La línea discontinua es dos pi, el valor del oscilador. [[curva]]El periodo real se separa poco al principio, y luego sube cada vez más rápido. [[punto]]A noventa grados, un dieciocho por ciento por encima. [[tope]]Y cerca de ciento ochenta grados se dispara: el péndulo casi llega arriba y se queda allí.""",
            [
                Plot(
                    id="p",
                    w=1000,
                    h=460,
                    xr=[0, 3.3],
                    yr=[5, 24],
                    xticks=[
                        [0.5236, "30°"],
                        [1.0472, "60°"],
                        [1.5708, "90°"],
                        [2.0944, "120°"],
                        [2.618, "150°"],
                        [3.1416, "180°"],
                    ],
                    yticks=[[6.2832, "2π"], [12.5664, "4π"], [18.8496, "6π"]],
                    xlabel="θ₀",
                    ylabel="T",
                    curves=[
                        dict(
                            pts=[[0, 6.2832], [3.3, 6.2832]],
                            color="muted",
                            width=3,
                            dash="10 8",
                            hidden=True,
                        ),
                        dict(pts=[[x, y] for x, y in CURVA_T], color="blue", hidden=True),
                    ],
                    points=[
                        dict(
                            x=1.5708,
                            y=round(T_90, 3),
                            color="gold",
                            label="90°",
                            dx=-40,
                            dy=-34,
                            hidden=True,
                        )
                    ],
                    vlines=[dict(x=3.1416, color="red", dash="8 7", hidden=True)],
                ),
            ],
            [
                A("curve", "p", at="linea", i=0, dur=0.8),
                A("curve", "p", at="curva", i=1, dur=2.5),
                A("point", "p", at="punto", i=0),
                A("vline", "p", at="tope", i=0),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Piensa qué pasa en el límite.""",
            [Plot(w=1, h=1, xr=[0, 1], yr=[0, 1])],
            ask=choice(
                "¿Qué ocurre con el periodo cuando la amplitud tiende a 180°?",
                [
                    "Tiende a $2\\pi$, como para ángulos pequeños",
                    "Tiende a un valor finito, el doble de $2\\pi$",
                    "Crece sin límite: arriba, el péndulo casi no tiene fuerza que lo saque de ahí",
                    "Tiende a cero, porque cae más deprisa",
                ],
                2,
                "En 180° el péndulo está en equilibrio inestable: la fuerza es $-\\sin\\pi=0$. Cuanto más cerca de arriba se suelta, más tarda en despegar. El periodo crece como un logaritmo y diverge.",
                wrong=[
                    "Eso solo ocurre cuando el ángulo es pequeño, no cerca de 180°.",
                    "No hay un valor finito: el periodo no se queda acotado.",
                    None,
                    "Cae más deprisa solo al principio; arriba, la fuerza es casi nula.",
                ],
            ),
        ),
        beat(
            "q2",
            ("", "Corrección de primer orden"),
            """Un desarrollo en serie da una corrección sencilla para amplitudes moderadas.""",
            [M(r"T\approx 2\pi\left(1+\frac{\theta_0^2}{16}\right)", size=54)],
            ask=numeric(
                "Con esta fórmula, ¿cuánto vale $T/2\\pi$ para $\\theta_0=1$ rad?",
                1.0625,
                "$1+1/16=1{,}0625$. La integración da $1{,}0663$: la corrección acierta con un error de $0{,}4\\,\\%$.",
                tol=0.001,
                hint="Sustituye $\\theta_0=1$: $1+\\theta_0^2/16$.",
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Escribe una función que mida el periodo de un péndulo soltado desde cualquier ángulo, con el método que acabamos de ver.""",
            [
                Exercise(
                    "f1-pendulo/periodo",
                    "Escribe `periodo(theta0, dt=0.001)`: suelta un péndulo con `g = L = 1` en reposo desde `theta0` radianes (entre 0 y π, sin incluir π), intégralo con leapfrog con aceleración `-sin(theta)` hasta que `theta` llegue a 0 o pase a ser negativo, y devuelve el periodo completo, 4 veces el instante del cruce. Mejora: el cruce cae entre dos pasos, interpola entre ellos.",
                    level=3,
                    needs="python",
                    id="e1",
                    hidden=True,
                    hints=[
                        "El péndulo tarda lo mismo en cada uno de los cuatro cuartos del vaivén, así que basta con medir el primero.",
                        "Un bucle `while True` que avanza el tiempo `t` en `dt` y termina cuando `theta` pasa a ser cero o negativo.",
                        "Si `theta` pasa de positivo a negativo en un paso, la fracción del paso hasta el cruce es `theta` dividido entre la diferencia de los dos valores.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma.""",
            [T("Una aproximación buena en un punto puede ser mala cuando te alejas.", "subtitle")],
            ask=reflect(
                "¿Qué pasaría con un reloj de péndulo si su amplitud cambiara de 5° a 30° por el desgaste? Usa la tabla.",
                "Medimos el periodo con un método de segundo orden y un paso de 0,001. ¿Cómo comprobarías que el paso es suficientemente pequeño?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Con ángulos pequeños el periodo vale dos pi, sea cual sea la amplitud. [[r2]]Fuera de ese límite crece con la amplitud: un dieciocho por ciento a noventa grados. [[r3]]Cerca de ciento ochenta grados se dispara. [[r4]]Con leapfrog se mide cruzando la vertical e interpolando entre dos pasos.""",
            s_cierre2,
            a_cierre2,
        ),
    ],
    practice=[
        "Mide el periodo con $\\Delta t=0{,}01$ y con $\\Delta t=0{,}0001$ y comprueba cuántas cifras coinciden.",
        "Compara la integración con la fórmula exacta $T=2\\pi/\\mathrm{AGM}(1,\\cos(\\theta_0/2))$, donde AGM es la media aritmético-geométrica.",
    ],
)

ORBITA = kepler("leapfrog", 0.01, 400)
ORBITA_EULER = kepler("euler", 0.01, 1200)
ORBITA_SALTO_3 = kepler("leapfrog", 0.01, 1200)
RADIOS = [math.hypot(x, y) for x, y, *_ in ORBITA]
CERCA = min(range(len(ORBITA)), key=lambda k: RADIOS[k])
L_EULER = momento(ORBITA_EULER, 0.01)
L_SALTO = momento(ORBITA_SALTO_3, 0.01)

s_cierre3, a_cierre3 = resumen(
    [
        "la energía y el momento angular de un planeta no cambian",
        "leapfrog conserva el momento angular exactamente y la energía con un error acotado",
        "Euler los hace crecer: la órbita se abre en espiral",
        "el periodo sale de la tercera ley: $T=2\\pi a^{3/2}$",
    ]
)
kepler_les = lesson(
    "f1-kepler",
    "Integrar un planeta: la órbita de Kepler",
    "La órbita de un planeta con leapfrog y con Euler: la energía y el momento angular se conservan en un caso y se escapan en el otro.",
    [
        "calcular la aceleración de un planeta y avanzar su órbita con leapfrog",
        "comprobar las magnitudes conservadas: energía y momento angular",
        "explicar por qué leapfrog conserva el momento angular y Euler no",
    ],
    [
        beat(
            "gravedad",
            ("", "La gravedad de un Sol"),
            """Un planeta de masa despreciable gira alrededor del Sol. [[ley]]Con unidades en las que la constante de gravitación por la masa del Sol vale uno, la aceleración apunta al Sol y vale uno entre la distancia al cuadrado.
             [[e]]Dos cantidades no cambian nunca. La energía, que suma la cinética y la potencial. [[l]]Y el momento angular, la posición en x por la velocidad en y, menos la posición en y por la velocidad en x.
             [[circ]]A distancia uno, la órbita circular tiene velocidad uno y periodo dos pi.""",
            [
                M(r"\vec a=-\frac{\vec r}{r^{3}}", id="ley", size=54, hidden=True),
                M(r"E=\tfrac12 v^2-\frac1r", id="e", size=46, hidden=True),
                M(r"L=x\,v_y-y\,v_x", id="l", size=46, hidden=True),
            ],
            [A("show", "ley", at="ley"), A("show", "e", at="e"), A("show", "l", at="l")],
        ),
        beat(
            "apuesta",
            ("", "Apuesta"),
            """Lanzamos el planeta desde distancia uno, con velocidad cero coma ocho, perpendicular a la dirección del Sol. [[apuesta]]Es menos que la velocidad circular. ¿Qué órbita sigue?""",
            [T("r = 1,  v = 0,8", "title")],
            ask=predict(
                "La órbita es…",
                [
                    "Una circunferencia, un poco más pequeña",
                    "Una elipse; el punto de partida es el más lejano del Sol",
                    "Una elipse; el punto de partida es el más cercano al Sol",
                    "Una espiral que cae al Sol",
                ],
                "Anotado. Integremos.",
            ),
        ),
        beat(
            "orbita",
            ("", "Una vuelta"),
            """Integramos con leapfrog y dibujamos una vuelta. [[sol]]El Sol está en un foco de la elipse, no en el centro. [[lejos]]Aquí empezó el planeta, en el punto más lejano. [[cerca]]Y aquí pasa más cerca y más deprisa: es la segunda ley de Kepler.""",
            [
                Plot(
                    id="p",
                    w=560,
                    h=560,
                    pw=440,
                    ph=440,
                    xr=[-1.4, 1.4],
                    yr=[-1.4, 1.4],
                    curves=[dict(pts=line([(x, y) for x, y, *_ in ORBITA]), color="teal")],
                    points=[
                        dict(x=0, y=0, color="gold", label="Sol", dx=0, dy=-34, hidden=True),
                        dict(x=1, y=0, color="blue", label="salida", dx=10, dy=-34, hidden=True),
                        dict(
                            x=round(ORBITA[CERCA][0], 3),
                            y=round(ORBITA[CERCA][1], 3),
                            color="red",
                            label="más cerca",
                            dx=-20,
                            dy=-36,
                            hidden=True,
                        ),
                    ],
                ),
            ],
            [
                A("point", "p", at="sol", i=0),
                A("point", "p", at="lejos", i=1),
                A("point", "p", at="cerca", i=2),
            ],
        ),
        beat(
            "fuerza",
            ("", "La aceleración"),
            """Ahora el código. [[acel]]La aceleración recibe la posición y devuelve las dos componentes: menos la posición entre la distancia al cubo. [[ener]]La energía suma la cinética y la potencial, menos uno entre la distancia.""",
            [
                Code(
                    """import math

def aceleracion(x, y):
    r3 = (x * x + y * y) ** 1.5
    return -x / r3, -y / r3

def energia(x, y, vx, vy):
    return 0.5 * (vx * vx + vy * vy) - 1 / math.hypot(x, y)""",
                    id="c",
                ),
            ],
            [A("hl", "c", at="acel", lines=[3, 4, 5]), A("hl", "c", at="ener", lines=[7, 8])],
        ),
        beat(
            "bucle",
            ("", "El bucle de leapfrog"),
            """El bucle repite los tres pasos. [[kick]]Medio paso de velocidad en las dos componentes, [[drift]]un paso de posición, [[nueva]]y la aceleración de la nueva posición, que se usa para el segundo medio paso y se guarda para el siguiente. [[out]]Tras tres vueltas, el error de energía es del orden de diez a la menos nueve, y el del momento angular, redondeo.""",
            [
                Code(
                    """x, y, vx, vy = 1.0, 0.0, 0.0, 0.8
dt, pasos = 0.01, 1200
E0, L0 = energia(x, y, vx, vy), x * vy - y * vx
ax, ay = aceleracion(x, y)
for _ in range(pasos):
    vx += 0.5 * dt * ax
    vy += 0.5 * dt * ay
    x += dt * vx
    y += dt * vy
    ax, ay = aceleracion(x, y)
    vx += 0.5 * dt * ax
    vy += 0.5 * dt * ay
print(f"error de energía: {energia(x, y, vx, vy) - E0:.1e}")
print(f"momento angular intacto: {abs(x * vy - y * vx - L0) < 1e-12}")""",
                    id="c",
                ),
                Out(
                    "error de energía: 4.8e-09\nmomento angular intacto: True",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="kick", lines=[6, 7]),
                A("hl", "c", at="drift", lines=[8, 9]),
                A("hl", "c", at="nueva", lines=[10]),
                A("show", "o", at="out"),
            ],
        ),
        beat(
            "euler_orbita",
            ("", "Lo mismo con Euler"),
            """Repetimos con Euler, el mismo paso de tiempo y el mismo número de pasos. [[codigo]]La posición avanza con la velocidad vieja, y la velocidad con la aceleración vieja. [[out]]El error de energía ya no es de diez a la menos nueve: es de cero coma veintiséis. Y el momento angular cambia en cero coma dieciséis, un veinte por ciento.""",
            [
                Code(
                    """x, y, vx, vy = 1.0, 0.0, 0.0, 0.8
for _ in range(pasos):
    ax, ay = aceleracion(x, y)
    x, y, vx, vy = x + dt * vx, y + dt * vy, vx + dt * ax, vy + dt * ay
print(f"error de energía: {energia(x, y, vx, vy) - E0:.2f}")
print(f"error de momento angular: {x * vy - y * vx - L0:.2f}")""",
                    id="c",
                ),
                Out(
                    "error de energía: 0.26\nerror de momento angular: 0.16",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [A("hl", "c", at="codigo", lines=[3, 4]), A("show", "o", at="out")],
        ),
        beat(
            "dos_orbitas",
            ("", "Las dos órbitas"),
            """Las dos órbitas, dibujadas durante tres vueltas. [[salto]]Leapfrog se cierra sobre sí misma: las tres vueltas caen una encima de otra. [[euler]]Con Euler, el planeta gana energía y se aleja un poco más en cada vuelta. La elipse se abre.""",
            [
                Plot(
                    id="p",
                    w=560,
                    h=560,
                    pw=440,
                    ph=440,
                    xr=[-1, 2],
                    yr=[-1.5, 1.5],
                    curves=[
                        dict(
                            pts=line([(x, y) for x, y, *_ in ORBITA_SALTO_3], 600),
                            color="teal",
                            hidden=True,
                        ),
                        dict(
                            pts=line([(x, y) for x, y, *_ in ORBITA_EULER], 600),
                            color="red",
                            hidden=True,
                        ),
                    ],
                    points=[dict(x=0, y=0, color="gold")],
                ),
            ],
            [A("curve", "p", at="salto", i=0, dur=1.5), A("curve", "p", at="euler", i=1, dur=3)],
        ),
        beat(
            "momento",
            ("", "El momento angular"),
            """Miremos el momento angular en el tiempo. [[salto]]Con leapfrog es una recta: cero coma ocho, siempre. [[euler]]Con Euler sube sin parar. La segunda ley de Kepler, áreas iguales en tiempos iguales, deja de cumplirse.""",
            [
                Plot(
                    id="p",
                    w=1000,
                    h=440,
                    xr=[0, 12],
                    yr=[0.6, 1.05],
                    xticks=[0, 3, 6, 9, 12],
                    yticks=[0.6, 0.8, 1.0],
                    xlabel="t",
                    ylabel="L",
                    curves=[
                        dict(
                            pts=line(L_SALTO),
                            color="teal",
                            hidden=True,
                            label="leapfrog",
                            lx=8.5,
                            ly=0.73,
                        ),
                        dict(
                            pts=line(L_EULER),
                            color="red",
                            hidden=True,
                            label="Euler",
                            lx=9,
                            ly=0.96,
                        ),
                    ],
                ),
            ],
            [A("curve", "p", at="salto", i=0, dur=1.2), A("curve", "p", at="euler", i=1, dur=2.5)],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Lo que hemos visto tiene una explicación.""",
            [M(r"L=\vec r\times\vec v", size=54)],
            ask=choice(
                "¿Por qué leapfrog conserva exactamente el momento angular $\\vec r\\times\\vec v$?",
                [
                    "Porque el paso de tiempo es pequeño",
                    "Porque cada sub-paso lo deja intacto: la aceleración es paralela a $\\vec r$, y mover $\\vec r$ en la dirección de $\\vec v$ tampoco lo cambia",
                    "Porque conserva también la energía exactamente",
                    "Porque usa una aceleración más precisa que Euler",
                ],
                1,
                "El kick suma a $\\vec v$ un vector paralelo a $\\vec r$: $\\vec r\\times\\Delta\\vec v=0$. El drift suma a $\\vec r$ un vector paralelo a $\\vec v$: $\\Delta\\vec r\\times\\vec v=0$. Euler mezcla ambos con valores viejos y deja un término $\\Delta t^2\\,\\vec v\\times\\vec a\\neq0$.",
                wrong=[
                    "Un paso pequeño reduce el error, pero no lo anula; aquí el error es exactamente cero.",
                    None,
                    "No: la energía de leapfrog oscila un poco, no es exacta.",
                    "Usa la misma aceleración que Euler; cambia el orden de las operaciones.",
                ],
            ),
        ),
        beat(
            "q2",
            ("", "Tercera ley"),
            """La tercera ley de Kepler relaciona el periodo con el tamaño de la elipse.""",
            [M(r"T=2\pi\,a^{3/2}\qquad a=\frac{1}{2-v_0^2}", size=46)],
            ask=numeric(
                "Con $v_0=0{,}8$, ¿cuánto dura una vuelta? Redondea a dos decimales.",
                3.96,
                "$a=1/(2-0{,}64)=0{,}7353$ y $T=2\\pi\\,a^{3/2}=3{,}96$. Con $\\Delta t=0{,}01$ son 396 pasos.",
                tol=0.002,
                hint="Calcula primero $a=1/(2-0{,}8^2)$ y luego $2\\pi\\,a^{3/2}$.",
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Escribe la función que avanza un planeta con leapfrog, y comprueba que la energía y el momento angular se quedan donde estaban.""",
            [
                Exercise(
                    "f1-kepler/orbita",
                    "Escribe `orbita(x, y, vx, vy, dt, pasos)`: integra con leapfrog un planeta con $GM=1$ (aceleración $-\\vec r/r^3$) y devuelve la tupla `(x, y, vx, vy)` tras `pasos` pasos. Trampa: la aceleración con que termina un paso es la del principio del siguiente.",
                    level=3,
                    needs="python",
                    id="e1",
                    hidden=True,
                    hints=[
                        "Es el mismo leapfrog de la primera lección, con las dos componentes de la posición y de la velocidad.",
                        "Define una función aparte que calcule la aceleración de una posición `(x, y)`, y llámala una vez por paso, tras mover la posición.",
                        "La aceleración tiene la forma `-x / r3`, `-y / r3`, con `r3` igual a `(x * x + y * y) ** 1.5`.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma.""",
            [
                T(
                    "Conservar una cantidad es una prueba, y también una pista del método.",
                    "subtitle",
                )
            ],
            ask=reflect(
                "Si no conocieras la solución, ¿cómo usarías la energía y el momento angular para saber si tu simulación de una órbita es fiable?",
                "Leapfrog conserva el momento angular de cualquier fuerza que apunte al Sol, sea cual sea su valor. ¿Qué te dice eso sobre lo que enseña la simulación y lo que no?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]La energía y el momento angular de un planeta no cambian. [[r2]]Leapfrog conserva el momento angular exactamente, y la energía con un error acotado. [[r3]]Euler hace crecer los dos, y la órbita se abre en espiral. [[r4]]El periodo sale de la tercera ley: dos pi por el semieje mayor elevado a tres medios.""",
            s_cierre3,
            a_cierre3,
        ),
    ],
    practice=[
        "Lanza el planeta con velocidad 1,2 y dibuja la órbita: ¿dónde está ahora el punto de salida respecto del Sol?",
        "Prueba velocidad $\\sqrt2$, la de escape: ¿qué pasa con la energía y con la forma de la órbita?",
    ],
)

LESSONS = [euler_leapfrog, pendulo_les, kepler_les]
