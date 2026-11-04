"""Parte IV · Primitivas y simulación."""

from lib import (
    A,
    Box,
    Circ,
    Code,
    Exercise,
    Flow,
    G,
    Hist,
    L,
    M,
    Mission,
    Out,
    Row,
    T,
    Table,
    beat,
    choice,
    lesson,
    numeric,
    predict,
    reflect,
)
from parte2 import resumen

# ------------------------------------------------------------------ 4.1 Primitivas
s_cierre, a_cierre = resumen(
    [
        "primitiva = la instrucción más simple útil a un nivel de abstracción",
        "Estimator → valores esperados · Sampler → muestras de bits",
        "clases base (V2) e implementaciones: IBM, `Statevector*`, `Backend*`, Aer",
        "mismas entradas para todas; las **opciones** cambian según la implementación",
    ]
)
primitivas = lesson(
    "p4-primitivas",
    "Las primitivas: Sampler y Estimator",
    "Por qué existen las primitivas, qué hacen Estimator y Sampler, y qué implementaciones hay: de referencia, de IBM, de backend y de Aer.",
    [
        "explicar qué problema resuelven las primitivas",
        "elegir entre Estimator y Sampler",
        "distinguir las clases base de sus implementaciones",
    ],
    [
        beat(
            "historia",
            ("", "Subir el nivel de abstracción"),
            """Al principio de la computación clásica, los programadores manipulaban registros de la CPU directamente. Con los computadores cuánticos pasó algo parecido: la primera interfaz devolvía los datos crudos de la electrónica de control.
             [[run]]Luego llegó backend punto run, que entregaba ceros y unos en un formato familiar. [[prim]]Y cuando creció el número de usuarios y de algoritmos, hizo falta subir un escalón más: las primitivas.
             [[reemp]]Hoy la interfaz de primitivas sustituye a backend punto run, porque Sampler ofrece el mismo acceso directo al hardware.""",
            [
                Flow(
                    [
                        dict(t="señales crudas", s="electrónica de control", color="muted"),
                        dict(t="backend.run", s="ceros y unos"),
                        dict(t="primitivas", s="Sampler · Estimator", color="gold"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="historia", i=0),
                A("item", "f", at="run", i=1),
                A("item", "f", at="prim", i=2),
                A("step", "f", at="reemp", i=2),
            ],
        ),
        beat(
            "dos",
            ("", "Dos tareas básicas"),
            """Una primitiva es la instrucción de procesamiento más pequeña con la que se construye algo útil a un nivel de abstracción. Las dos tareas más comunes de un computador cuántico son estimar valores esperados y muestrear estados.
             [[est]]Estimator calcula valores esperados de observables sobre los estados que preparan los circuitos. [[sam]]Sampler muestrea el registro de salida de un circuito: devuelve los bits medidos.
             [[idea]]La idea es acercar la programación cuántica a la clásica: menos detalles del hardware, más foco en el resultado.""",
            [
                Row(
                    Box(
                        "def",
                        "Estimator",
                        M(r"\langle\psi(\theta)|\,O\,|\psi(\theta)\rangle", size=34),
                        T("circuitos **sin** mediciones + observables", "note"),
                    ),
                    Box(
                        "idea",
                        "Sampler",
                        Code("0110\n1001\n0110\n…", "out"),
                        T("circuitos **con** mediciones", "note"),
                    ),
                    id="r",
                    hidden=True,
                    gap=30,
                )
            ],
            [A("show", "r", at="est")],
        ),
        beat(
            "predice",
            ("", "Antes de ejecutar"),
            """Probemos las dos primitivas sobre el mismo estado: un estado de Bell. [[obs]]A Estimator le damos el circuito sin mediciones y tres observables: Z Z, Z sobre el qubit uno, y X X.
             [[apuesta]]Apuesta: ¿qué tres valores esperados devolverá?""",
            [
                Row(
                    Circ(2, [G("h", 0), G("cx", 0, 1)], id="q"),
                    Table(
                        ["Observable", "Significa"],
                        [
                            ["`ZZ`", "los dos qubits a la vez"],
                            ["`ZI`", "solo el qubit 1"],
                            ["`XX`", "medir ambos en la base X"],
                        ],
                        id="t",
                        hidden=True,
                        size=24,
                    ),
                    gap=30,
                )
            ],
            [A("show", "t", at="obs")],
            ask=predict(
                "¿Qué devuelve Estimator para `ZZ`, `ZI` y `XX`?",
                ["[1, 1, 1]", "[1, 0, 1]", "[0, 0, 0]", "[1, 0, 0]"],
                "Anotado. Veámoslo, y comparémoslo con lo que da Sampler.",
            ),
        ),
        beat(
            "mismo_estado",
            ("", "El mismo estado, dos preguntas"),
            """Este es el código. [[est]]Estimator devuelve uno, cero y uno. Z Z vale uno porque los dos qubits siempre coinciden. Z sobre el qubit uno vale cero, porque por sí solo es una moneda perfecta. Y X X vale uno. Si apostaste por la opción b, acertaste.
             [[sam]]Sampler, en cambio, no devuelve números esperados: devuelve cadenas medidas, cero cero y uno uno, mitad y mitad.
             [[idea]]Es el mismo estado visto de dos maneras: la primitiva que elijas decide qué pregunta le haces.""",
            [
                Code(
                    """bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)
obs = [SparsePauliOp(p) for p in ["ZZ", "ZI", "XX"]]
print(StatevectorEstimator().run([(bell, obs)]).result()[0].data.evs)

bell.measure_all()
print(StatevectorSampler(seed=3).run([bell], shots=1024).result()[0].data.meas.get_counts())""",
                    id="c",
                    size=22,
                    setup="from qiskit import QuantumCircuit\nfrom qiskit.quantum_info import SparsePauliOp\nfrom qiskit.primitives import StatevectorEstimator, StatevectorSampler",
                ),
                Out("[1. 0. 1.]\n{'00': 515, '11': 509}", id="o", hidden=True, check=True),
                T("Estimator: números · Sampler: cadenas de bits", "note", id="n", hidden=True),
            ],
            [
                A("hl", "c", at="est", range="4-5"),
                A("show", "o", at="est"),
                A("hl", "c", at="sam", range="7-8"),
                A("show", "n", at="idea"),
            ],
        ),
        beat(
            "impl",
            ("", "Clases base e implementaciones"),
            """Hay dos niveles. [[base]]Las clases base, en qiskit punto primitives, definen la interfaz común: BaseEstimatorV2 y BaseSamplerV2. Las V1 aún existen, pero el curso usa las V2.
             [[impl]]Sobre ellas se construyen implementaciones, todas con la misma forma de uso. [[ibm]]Las de IBM, en qiskit ibm runtime, ejecutan en hardware real con mitigación de errores.
             [[ref]]Las de referencia, StatevectorEstimator y StatevectorSampler, simulan con vectores de estado ideales en tu computadora. [[back]]BackendEstimatorV2 y BackendSamplerV2 envuelven cualquier backend en una primitiva. [[aer]]Y Qiskit Aer tiene las suyas, con ruido.""",
            [
                Table(
                    ["Implementación", "Dónde corre", "Para qué"],
                    [
                        [
                            "`executor_estimator.Estimator` / `executor_sampler.Sampler`",
                            "hardware de IBM",
                            "mitigación, resiliencia",
                        ],
                        [
                            "`StatevectorEstimator` / `StatevectorSampler`",
                            "tu computadora",
                            "simulación exacta, prototipos",
                        ],
                        [
                            "`BackendEstimatorV2` / `BackendSamplerV2`",
                            "cualquier `BackendV2`",
                            "proveedores sin primitivas propias",
                        ],
                        [
                            "`qiskit_aer.primitives`",
                            "tu computadora",
                            "simulación rápida y con ruido",
                        ],
                    ],
                    id="t",
                    stagger=True,
                    size=22,
                ),
                T(
                    "todas heredan de `BaseEstimatorV2` / `BaseSamplerV2`",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("show", "n", at="base"),
                A("item", "t", at="ibm", i=0),
                A("item", "t", at="ref", i=1),
                A("item", "t", at="back", i=2),
                A("item", "t", at="aer", i=3),
            ],
        ),
        beat(
            "backend",
            ("", "Primitivas de backend"),
            """Las primitivas de backend son genéricas: funcionan con cualquier objeto que implemente la interfaz BackendV2, aunque su proveedor no tenga primitivas propias.
             [[est]]BackendEstimatorV2 no trae mitigación de errores incorporada, porque corre en tu máquina. [[sam]]Y BackendSamplerV2 necesita que el backend admita la opción memory, para devolver cada disparo.""",
            [
                Code(
                    """from qiskit.primitives import BackendEstimatorV2, BackendSamplerV2
from qiskit.providers.fake_provider import GenericBackendV2

backend = GenericBackendV2(5)
estimator = BackendEstimatorV2(backend=backend)
sampler = BackendSamplerV2(backend=backend)""",
                    id="c",
                ),
                Row(
                    Box(
                        "warn",
                        "Estimator de backend",
                        T("sin mitigación incorporada", "body"),
                        id="a",
                        hidden=True,
                    ),
                    Box(
                        "warn",
                        "Sampler de backend",
                        T("el backend debe admitir `memory`", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=26,
                ),
            ],
            [A("show", "a", at="est"), A("show", "b", at="sam")],
        ),
        beat(
            "opciones",
            ("", "Opciones y ventajas"),
            """El método run es igual en todas las implementaciones, pero las opciones no: cada una documenta las suyas.
             [[ventaja]]Esa capa extra de abstracción tiene ventajas. Con las primitivas de IBM, por ejemplo, activas técnicas avanzadas de mitigación cambiando una opción, como resilience level, en lugar de implementarlas tú.
             [[prov]]Y para los fabricantes de hardware, implementar primitivas es una forma de ofrecer sus mejores capacidades directamente a los usuarios.""",
            [
                Code(
                    """from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

estimator = Estimator(mode=FakeManilaV2())
estimator.options.resilience_level = 2   # IBM: mitigación con una línea""",
                    id="c",
                ),
                T(
                    "`run()` es común · las opciones dependen de la implementación",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [A("show", "n", at="opciones"), A("hl", "c", at="ventaja", lines=[5])],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Una pregunta sobre implementaciones.""",
            [
                T(
                    "Tienes un backend de otro fabricante que solo ofrece `backend.run()`, y quieres usar código estilo primitivas.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué usas?",
                [
                    "`StatevectorSampler`",
                    "`BackendSamplerV2(backend=...)`",
                    "`executor_sampler.Sampler`",
                ],
                1,
                "Correcto: las primitivas de backend envuelven cualquier `BackendV2`.",
                wrong=[
                    "Esa simula localmente; no usa el backend del fabricante.",
                    None,
                    "Esa es para el servicio de IBM.",
                ],
            ),
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Otra pregunta.""",
            [
                T(
                    "Quieres la distribución completa de cadenas de bits de un algoritmo de búsqueda.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué primitiva?",
                ["Estimator", "Sampler"],
                1,
                "Correcto: Sampler devuelve las muestras de bits; con ellas construyes la distribución.",
                wrong=["Estimator devuelve valores esperados, no muestras."],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            "Ahora te toca a ti. [[n1]]Primero apuestas los tres valores esperados que Estimator da para el estado de Bell, y los comparas con lo que calcula. [[n2]]Después cambias la implementación de Sampler por BackendSamplerV2, sin tocar el resto del código. [[n3]]Y por último escribes la función que calcula un valor esperado a partir de los conteos de Sampler, y compruebas que coincide con el de Estimator.",
            [
                Exercise(
                    "p4-primitivas/dos-vistas",
                    "Este código calcula con Estimator tres valores esperados del estado de Bell y mide el mismo estado con Sampler. Apuesta en `prediccion` una lista con $\\langle ZZ\\rangle$, $\\langle ZI\\rangle$ y $\\langle XX\\rangle$, y compruébala después.",
                    level=1,
                    needs="qiskit",
                    id="e1",
                    hidden=True,
                    hints=[
                        "Piensa en lo que ve cada observable: Z mide el valor de un qubit y X, la fase entre las ramas.",
                        "En el estado de Bell, los dos qubits siempre coinciden; mira qué pasa cuando miras un solo qubit y cuando miras los dos.",
                        "La lista tiene tres números, en el orden `[ZZ, ZI, XX]`.",
                    ],
                ),
                Exercise(
                    "p4-primitivas/backend-sampler",
                    "Cambia la línea de `sampler` para que use `BackendSamplerV2` sobre `backend`, sin tocar el resto: `run` recibe lo mismo y devuelve lo mismo. El circuito ya está transpilado para ese backend.",
                    level=2,
                    needs="qiskit",
                    id="e2",
                    hidden=True,
                    hints=[
                        "`BackendSamplerV2` envuelve un backend en la interfaz de las primitivas.",
                        "Solo cambia la línea que crea `sampler`; la llamada a `run` y el resto del programa se quedan igual.",
                        "El constructor recibe el backend con el argumento `backend=`.",
                    ],
                ),
                Exercise(
                    "p4-primitivas/z-desde-conteos",
                    'Escribe `z_desde_conteos(conteos, k)`: recibe el diccionario de `get_counts()` y el índice de un qubit, y devuelve $\\langle Z_k\\rangle$ como un número entre -1 y 1. Cada disparo con el bit `0` en ese qubit aporta $+1$ y cada disparo con `1` aporta $-1$; el resultado es el promedio sobre todos los disparos. Ojo: el qubit 0 es el carácter de la **derecha** de la cadena. Por ejemplo, con `{"00": 3, "01": 1}` y `k = 0` devuelve 0.5.',
                    level=3,
                    needs="qiskit",
                    id="e3",
                    hidden=True,
                    hints=[
                        "Un valor esperado de Z es un promedio: el bit 0 vale $+1$ y el bit 1 vale $-1$.",
                        "Recorre los pares cadena y cantidad del diccionario, y elige el carácter del qubit `k` contando desde la derecha.",
                        "Suma cantidad por signo para cada cadena y divide entre el total de disparos, que es la suma de las cantidades.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda y lo verás cuando vuelvas a esta lección.""",
            [T("La primitiva que eliges decide la pregunta que haces.", "subtitle")],
            ask=reflect(
                "En el estado de Bell, ¿por qué Estimator da `0` para `ZI` mientras que `ZZ` da `1`? Explícalo con lo que verías en los conteos de Sampler.",
                "El método `run` es igual en todas las implementaciones, pero las opciones no. ¿Qué ventaja y qué riesgo ves en eso al cambiar de un simulador a un QPU?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Una primitiva es el bloque básico de un nivel de abstracción. [[r2]]Estimator da valores esperados y Sampler, muestras. [[r3]]Hay clases base y varias implementaciones.
             [[r4]]Todas se usan igual; sus opciones cambian. En la próxima lección, sus entradas y salidas en detalle.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["primitives", "get-started-with-backend-primitives"],
    practice=[
        "Ejecuta el mismo circuito de Bell con `StatevectorSampler` y con `BackendSamplerV2(backend=GenericBackendV2(2))` y compara los conteos.",
        "Lee la referencia de [primitivas de Qiskit](https://quantum.cloud.ibm.com/docs/en/api/qiskit/primitives) y busca qué opciones admite `StatevectorEstimator`.",
    ],
)

# ------------------------------------------------------------------ 4.2 PUBs
s_cierre, a_cierre = resumen(
    [
        "PUB de Estimator: (circuito, observables, parámetros, precisión)",
        "PUB de Sampler: (circuito, parámetros, disparos)",
        "observables y parámetros se combinan con las reglas de broadcasting de NumPy",
        "`PrimitiveResult` → `PubResult` → `data` (`evs`, `stds` o un `BitArray` por registro) + `metadata`",
    ]
)
pubs = lesson(
    "p4-pubs",
    "Entradas y salidas: PUBs y broadcasting",
    "Los Primitive Unified Blocs, las reglas de broadcasting, la estructura de los resultados y el procesamiento eficiente con BitArray.",
    [
        "armar PUBs para Estimator y Sampler",
        "predecir la forma del resultado con las reglas de broadcasting",
        "leer y posprocesar resultados con `BitArray`",
    ],
    [
        beat(
            "pub",
            ("", "Primitive Unified Blocs"),
            """El argumento principal de run es una lista de tuplas, una por circuito. Cada tupla es un PUB, un bloque unificado de primitiva: la unidad básica de trabajo.
             [[est]]El PUB de Estimator tiene hasta cuatro elementos: un circuito, que puede tener parámetros; un arreglo de observables; los valores de los parámetros, si hacen falta; y, opcionalmente, la precisión deseada.
             [[sam]]El de Sampler tiene hasta tres: un circuito, que debe incluir mediciones; los valores de los parámetros; y, opcionalmente, el número de disparos.""",
            [
                Row(
                    Box(
                        "def",
                        "PUB de Estimator",
                        Code("(circuito, observables, parámetros, precisión)", "text"),
                    ),
                    Box("idea", "PUB de Sampler", Code("(circuito, parámetros, disparos)", "text")),
                    gap=24,
                    id="r",
                ),
                Code("estimator.run([pub1, pub2, ...])", id="c", norun=True),
            ],
            [],
        ),
        beat(
            "conmutan",
            ("", "Agrupar observables"),
            """Un detalle importante. Si dos observables que conmutan van en PUBs distintos con el mismo circuito, no se miden juntos: cada PUB representa una base de medición distinta y necesita sus propias mediciones.
             [[mismo]]Para que se estimen con la misma medición, ponlos en el mismo PUB.""",
            [
                Row(
                    Box(
                        "warn",
                        "Dos PUBs",
                        Code('[(qc, "ZZ"), (qc, "ZI")]', "text"),
                        T("dos rondas de medición", "note"),
                    ),
                    Box(
                        "def",
                        "Un PUB",
                        Code('[(qc, ["ZZ", "ZI"])]', "text"),
                        T("una ronda: conmutan", "note"),
                        id="b",
                        hidden=True,
                    ),
                    gap=26,
                )
            ],
            [A("show", "b", at="mismo")],
        ),
        beat(
            "broadcast",
            ("", "Broadcasting"),
            """Los observables y los valores de parámetros se combinan con las mismas reglas de broadcasting que NumPy.
             [[derecha]]Las formas se comparan de derecha a izquierda. [[comp]]Dos dimensiones son compatibles si son iguales o si una vale uno. [[falta]]Si un arreglo tiene menos dimensiones, se completan con unos a la izquierda.
             [[res]]El resultado tiene, en cada dimensión, el tamaño mayor. Estimator devuelve un valor esperado por cada elemento de esa forma.""",
            [
                Table(
                    ["A", "B", "resultado"],
                    [
                        ["(5,)", "( )", "(5,)"],
                        ["(5,)", "(5,)", "(5,) · elemento a elemento"],
                        ["(1, 6)", "(4, 1)", "(4, 6) · producto exterior"],
                        ["(3, 6)", "(2, 3, 1)", "(2, 3, 6)"],
                        ["(5,)", "(3,)", "**error**: incompatibles"],
                    ],
                    id="t",
                    stagger=True,
                    size=25,
                )
            ],
            [
                A("item", "t", at="derecha", i=0),
                A("item", "t", at="comp", i=1),
                A("item", "t", at="comp", t=1.5, i=2),
                A("item", "t", at="falta", i=3),
                A("item", "t", at="res", i=4),
            ],
        ),
        beat(
            "forma",
            ("", "La forma de un observable"),
            """Ojo con qué cuenta como un elemento. Un SparsePauliOp es un solo elemento, sin importar cuántos términos tenga: su forma es vacía.
             [[lista]]En cambio, una lista de tres SparsePauliOp tiene forma tres: tres observables distintos, tres valores esperados.
             [[col]]Y una lista de listas de un elemento tiene forma tres por uno: la columna que se combina con los parámetros en producto exterior.""",
            [
                Code(
                    """a = SparsePauliOp.from_list([("XX", 1), ("XY", 1), ("IZ", 1)])  # forma ()
b = [SparsePauliOp("XX"), SparsePauliOp("XY"), SparsePauliOp("IZ")]  # forma (3,)
c = [[SparsePauliOp("XX")], [SparsePauliOp("XY")], [SparsePauliOp("IZ")]]  # forma (3, 1)""",
                    id="c",
                    setup="from qiskit.quantum_info import SparsePauliOp",
                    size=22,
                )
            ],
            [
                A("hl", "c", at="forma", lines=[1]),
                A("hl", "c", at="lista", lines=[2]),
                A("hl", "c", at="col", lines=[3]),
            ],
        ),
        beat(
            "ejemplo_pred",
            ("", "Antes de ejecutar"),
            """Una apuesta con broadcasting. Tenemos un circuito de tres qubits con un parámetro, y cuatro observables escritos como una columna, con forma cuatro por uno.
             [[par]]Los valores del parámetro son seis, con forma uno por seis. [[apuesta]]¿Qué forma tendrá evs?""",
            [
                Table(
                    ["Entrada", "Forma"],
                    [
                        ["observables", "(4, 1)"],
                        ["valores del parámetro", "(1, 6)"],
                        ["`evs`", "¿?"],
                    ],
                    id="t",
                    size=28,
                )
            ],
            [],
            ask=predict(
                "¿Qué forma tiene `evs`?",
                ["(4, 6)", "(6, 4)", "(24,)", "error: son incompatibles"],
                "Anotado. Ejecutémoslo y veamos.",
            ),
        ),
        beat(
            "ejemplo",
            ("", "Un ejemplo vectorizado"),
            """Veamos el ejemplo completo. Un circuito con un parámetro, a, y observables. [[zip]]Con cinco valores del parámetro y cinco observables, en forma cinco, se emparejan uno a uno: cinco resultados.
             [[outer]]Con valores en forma uno por seis y observables en forma cuatro por uno, se combina cada valor con cada observable: veinticuatro resultados, en forma cuatro por seis. Si apostaste por la opción a, acertaste.
             [[una]]Todo en una sola llamada a run: así se ejecutan barridos enormes de forma eficiente.""",
            [
                Code(
                    """import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import SparsePauliOp
from qiskit.primitives import StatevectorEstimator

circ = QuantumCircuit(3)
circ.ry(Parameter("a"), 0)
circ.cx(0, 1)
circ.cx(1, 2)
estimator = StatevectorEstimator()

zip_obs = [SparsePauliOp(p) for p in ["III", "XXX", "YYY", "ZZZ", "XYZ"]]
r1 = estimator.run([(circ, zip_obs, np.linspace(0, 1, 5)[:, None])]).result()
outer_obs = [[SparsePauliOp(p)] for p in ["III", "XXX", "YYY", "ZZZ"]]
r2 = estimator.run([(circ, outer_obs, np.linspace(0, 1, 6)[None, :, None])]).result()
print(r1[0].data.evs.shape, r2[0].data.evs.shape)""",
                    id="c",
                    size=20,
                ),
                Out("(5,) (4, 6)", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="zip", range="13-14"),
                A("hl", "c", at="outer", range="15-16"),
                A("show", "o", at="una"),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Aplica las reglas de broadcasting.""",
            [
                T(
                    "Valores de parámetros con forma `(10, 2)` (10 juegos de 2 parámetros) y observables con forma `(3, 1)`.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué forma tiene `evs`?",
                ["(10,)", "(3, 10)", "(3, 1)", "error"],
                1,
                "Correcto: la última dimensión de los parámetros (2) recorre los parámetros del circuito, así que su forma de broadcasting es (10,). Con (3, 1) da (3, 10).",
                wrong=[
                    "Faltan los tres observables.",
                    None,
                    "Faltan los diez juegos de parámetros.",
                    "Son compatibles: (10,) con (3, 1).",
                ],
            ),
        ),
        beat(
            "salida",
            ("", "La estructura de la salida"),
            """Cuando un trabajo termina, devuelve un PrimitiveResult: una lista con un PubResult por cada PUB que enviaste.
             [[pub]]Cada PubResult tiene data y metadata. [[est]]Para Estimator, data contiene evs, los valores esperados, y stds, sus desviaciones, con la forma del PUB.
             [[sam]]Para Sampler, data contiene un BitArray por cada registro clásico del circuito, con el nombre del registro: meas, si usaste measure all.
             [[meta]]Y la metadata depende de la implementación: por ejemplo, los disparos usados.""",
            [
                Code(
                    """PrimitiveResult
├── PubResult[0]
│   ├── data     → evs, stds          (Estimator)
│   │            → meas, alpha, …     (Sampler: un BitArray por registro)
│   └── metadata → shots, target_precision, …
├── PubResult[1]
└── …""",
                    "text",
                    id="c",
                    size=24,
                )
            ],
            [
                A("hl", "c", at="pub", lines=[2]),
                A("hl", "c", at="est", lines=[3]),
                A("hl", "c", at="sam", lines=[4]),
                A("hl", "c", at="meta", lines=[5]),
            ],
        ),
        beat(
            "bitarray",
            ("", "BitArray"),
            """BitArray guarda los disparos en orden, empaquetados como bytes en un arreglo de dos dimensiones: una fila por disparo y una columna por byte.
             [[ej]]Aquí, un GHZ de diez qubits con dos registros: alpha, con el qubit cero, y beta, con los otros nueve. Beta ocupa dos bytes por disparo.
             [[conv]]get counts y get bitstrings convierten a cadenas cuando hace falta.""",
            [
                Code(
                    """from qiskit import QuantumRegister, ClassicalRegister
from qiskit.primitives import StatevectorSampler

circuit = QuantumCircuit(
    QuantumRegister(10),
    alpha := ClassicalRegister(1, "alpha"),
    beta := ClassicalRegister(9, "beta"))
circuit.h(0)
circuit.cx(range(0, 9), range(1, 10))
circuit.measure([0], alpha)
circuit.measure(range(1, 10), beta)
data = StatevectorSampler(seed=11).run([circuit]).result()[0].data
print(data.alpha.array.shape, data.beta.array.shape)
print(data.beta.get_counts())""",
                    id="c",
                    size=22,
                ),
                Out(
                    "(1024, 1) (1024, 2)\n{'000000000': 532, '111111111': 492}",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="ej", range="4-11"),
                A("show", "o", at="ej", t=3),
                A("hl", "c", at="conv", lines=[14]),
            ],
        ),
        beat(
            "post",
            ("", "Posprocesar sin diccionarios"),
            """Los arreglos son mucho más rápidos que los diccionarios, así que conviene posprocesar directamente con BitArray.
             [[mask]]Puedes postseleccionar: quedarte con los disparos de beta en los que alpha valió uno. [[slice]]Recortar bits, con slice bits, o disparos, con slice shots.
             [[ev]]Calcular valores esperados de operadores diagonales, con expectation values. [[cat]]Y unir registros con concatenate bits.""",
            [
                Code(
                    """mask = data.alpha.array == 1
print(data.beta[mask[:, 0]].get_counts())
print(data.beta.slice_bits([0, 1, 2]).get_counts())
print(data.beta.slice_shots([0, 1, 2, 3, 4]).num_shots)
print(data.beta.expectation_values([SparsePauliOp("Z" * 9)]))
from qiskit.primitives import BitArray
print(BitArray.concatenate_bits([data.alpha, data.beta]).num_bits)""",
                    id="c",
                    size=22,
                ),
                Out(
                    "{'111111111': 492}\n{'000': 532, '111': 492}\n5\n[0.0390625]\n10",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="mask", lines=[1, 2]),
                A("hl", "c", at="slice", lines=[3, 4]),
                A("hl", "c", at="ev", lines=[5]),
                A("hl", "c", at="cat", lines=[6, 7]),
                A("show", "o", at="cat", t=1),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Sobre la salida de Sampler.""",
            [
                Code(
                    """qc = QuantumCircuit(2, 2)
qc.h(0)
qc.measure([0, 1], [0, 1])""",
                    setup="from qiskit import QuantumCircuit",
                )
            ],
            ask=choice(
                "¿Cómo lees los conteos?",
                [
                    "`result[0].data.meas.get_counts()`",
                    "`result[0].data.c.get_counts()`",
                    "`result[0].data.evs`",
                ],
                1,
                "Correcto: el registro clásico creado por `QuantumCircuit(2, 2)` se llama `c`. `meas` solo existe si usas `measure_all()`.",
                wrong=[
                    "No hay registro `meas`: no se usó `measure_all()`.",
                    None,
                    "`evs` es de Estimator.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            "Ahora te toca a ti. [[n1]]Primero apuestas las formas que tienen los dos barridos de la lección. [[n2]]Después corriges la forma de los observables para que evs salga con forma tres por diez. [[n3]]Y por último, con un solo PUB de Sampler, calculas la probabilidad de medir uno para varios ángulos, posprocesando el BitArray sin diccionarios.",
            [
                Exercise(
                    "p4-pubs/formas",
                    "Este código ejecuta los dos barridos de la lección, `uno_a_uno` y `producto`. Apuesta en `prediccion` la forma de cada `evs`, como una pareja de formas, y compruébala después.",
                    level=1,
                    needs="qiskit",
                    id="e1",
                    hidden=True,
                    hints=[
                        "Las formas se emparejan por broadcasting, empezando por el último eje.",
                        "Mira la forma de los observables y la de los valores del parámetro en cada PUB; en `producto` uno tiene un eje de tamaño 1 y el otro lo estira.",
                        "Escribe `((forma_de_uno_a_uno), (forma_de_producto))`, con una tupla por barrido.",
                    ],
                ),
                Exercise(
                    "p4-pubs/observables-3x10",
                    "Este código quiere un `evs_barrido` con una fila por observable (`ZZZ`, `XXX`, `YYY`) y una columna por cada uno de los 10 valores de `a`, pero sale con forma `(10,)`. Corrige cómo se arma `observables`.",
                    level=2,
                    needs="qiskit",
                    id="e2",
                    hidden=True,
                    kind="fix",
                    hints=[
                        "Un solo `SparsePauliOp` con tres términos es un único observable: tiene forma `()`.",
                        "Necesitas tres observables, con forma `(3, 1)`, para que el broadcasting los cruce con los valores de forma `(10,)`.",
                        "Una lista de listas de un solo elemento, una lista por cada Pauli.",
                    ],
                ),
                Exercise(
                    "p4-pubs/probabilidad-uno",
                    'Escribe `probabilidad_uno(angulos, disparos)`: `angulos` es un arreglo de NumPy de cualquier forma y `disparos` es un entero. Devuelve un arreglo con la forma de `angulos` con la probabilidad de medir 1 tras $R_y(\\theta)$ en un qubit, usando **un solo PUB** de `StatevectorSampler` y sin `get_counts`: con `expectation_values("Z")` del `BitArray` y $P(1)=(1-\\langle Z\\rangle)/2$. Ojo: los valores de un parámetro necesitan un último eje de tamaño 1, así que `angulos` de forma `(2, 3)` se entrega como `(2, 3, 1)`.',
                    level=3,
                    needs="qiskit",
                    id="e3",
                    hidden=True,
                    hints=[
                        "Un solo PUB barre todos los ángulos a la vez: el circuito, los valores del parámetro y los disparos.",
                        "`datos.meas` es un `BitArray` con la forma de los ángulos y tiene el método `expectation_values`.",
                        "Añade el eje del parámetro con `[..., None]` y devuelve `(1 - ...) / 2`.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma. Escribe con tus palabras; se guardan en tu navegador.""",
            [T("Una forma bien pensada ahorra cientos de ejecuciones.", "subtitle")],
            ask=reflect(
                "Explica con tus palabras por qué observables de forma `(3, 1)` y parámetros de forma `(10,)` dan `(3, 10)` y no `(10, 3)`.",
                "Quieres estimar `ZZ` y `ZI` del mismo circuito. ¿Los pondrías en el mismo PUB o en PUBs distintos? ¿Por qué?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Un PUB de Estimator lleva circuito, observables, parámetros y precisión. [[r2]]Uno de Sampler, circuito, parámetros y disparos. [[r3]]Las formas se combinan con broadcasting.
             [[r4]]Y la salida es un PrimitiveResult con un PubResult por PUB, que se posprocesa mejor con BitArray.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["primitive-input-output"],
    practice=[
        "Reproduce el ejemplo de la guía original con observables de forma (3, 1) y 10 juegos de dos parámetros, y grafica cada fila de `evs`.",
        "Postselecciona un GHZ de 5 qubits quedándote con los disparos en que el qubit 0 midió 0, usando solo `BitArray`.",
    ],
)

# ------------------------------------------------------------------ 4.3 Simulación exacta
# Context of the shots-per-PUB fragment: two circuits with measurement and a local Sampler.
SHOTS_SETUP = """from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

sampler = StatevectorSampler()
qc1 = QuantumCircuit(1)
qc1.h(0)
qc1.measure_all()
qc2 = qc1.copy()"""
s_cierre, a_cierre = resumen(
    [
        "simular sirve hasta ~50 qubits · 4 GB de RAM ≈ 27 qubits",
        "`StatevectorEstimator`: exacto; `precision=` añade ruido de muestreo",
        "`StatevectorSampler`: `shots=` global o por PUB `(qc, None, 123)`",
        "las de referencia aceptan circuitos abstractos (transpilar es opcional)",
    ]
)
exacta = lesson(
    "p4-simular-exacto",
    "Simulación exacta con las primitivas del SDK",
    "Cuándo y cómo simular: límites de memoria, StatevectorEstimator y StatevectorSampler, precisión, disparos y lectura de resultados.",
    [
        "saber hasta dónde llega la simulación clásica",
        "ejecutar `StatevectorEstimator` con parámetros y precisión",
        "ejecutar `StatevectorSampler` y controlar los disparos por PUB",
    ],
    [
        beat(
            "por_que",
            ("", "Simular antes de ejecutar"),
            """Antes de enviar un programa a un QPU conviene probarlo en un simulador: es rápido y permite depurar. [[limite]]Pero simular cuesta exponencialmente en el número de qubits: más allá de unos cincuenta, en general no se puede.
             [[opciones]]Para circuitos grandes hay dos salidas: probar versiones más pequeñas, o modificarlos para que sean simulables, por ejemplo convirtiéndolos en circuitos de Clifford, que se simulan con miles de qubits.
             [[mem]]Una referencia: con cuatro gigabytes de RAM se simulan unos veintisiete qubits. Más memoria no da resultados más exactos; solo permite más qubits o más rapidez.""",
            [
                Table(
                    ["Herramienta", "Para"],
                    [
                        [
                            "`StatevectorEstimator` / `StatevectorSampler`",
                            "circuitos pequeños, exacto",
                        ],
                        ["Qiskit Aer", "circuitos más grandes, con ruido, GPU"],
                        ["Simulador de estabilizadores", "circuitos de Clifford, miles de qubits"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                ),
                M(
                    r"\text{memoria}\propto 2^n:\quad 4\ \text{GB}\approx 27\ \text{qubits}",
                    id="m",
                    hidden=True,
                    size=36,
                ),
            ],
            [
                A("item", "t", at="limite", i=0),
                A("item", "t", at="opciones", i=1),
                A("item", "t", at="opciones", t=2, i=2),
                A("show", "m", at="mem"),
            ],
        ),
        beat(
            "estimator",
            ("", "StatevectorEstimator"),
            """Empecemos con Estimator. El circuito tiene un parámetro, theta, y no lleva mediciones. [[obs]]El observable es II más XX menos YY más ZZ. [[par]]Lo evaluamos con tres valores de theta: cero, pi sextos y pi medios.
             [[run]]run recibe un PUB con las tres cosas, y result devuelve los valores esperados: cuatro, tres coma setenta y tres, y dos.
             [[isa]]Las primitivas de referencia aceptan circuitos abstractos; transpilar es opcional, aunque puede ayudar a optimizar.""",
            [
                Code(
                    """import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import SparsePauliOp
from qiskit.primitives import StatevectorEstimator

circuit = QuantumCircuit(2)
circuit.ry(Parameter("theta"), 0)
circuit.h(0)
circuit.cx(0, 1)
observable = SparsePauliOp(["II", "XX", "YY", "ZZ"], coeffs=[1, 1, -1, 1])
parameter_values = [[0], [np.pi / 6], [np.pi / 2]]

estimator = StatevectorEstimator()
result = estimator.run([(circuit, observable, parameter_values)]).result()
print(result[0].data.evs)
print(result[0].metadata)""",
                    id="c",
                    size=21,
                ),
                Out(
                    "[4.         3.73205081 2.        ]\n{'target_precision': 0.0, 'circuit_metadata': {}}",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="estimator", range="7-10"),
                A("hl", "c", at="obs", lines=[11]),
                A("hl", "c", at="par", lines=[12]),
                A("hl", "c", at="run", range="14-16"),
                A("show", "o", at="run", t=2),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Verifica el primer valor.""",
            [
                M(
                    r"\theta=0:\ \ |\psi\rangle=\tfrac{1}{\sqrt2}(|00\rangle+|11\rangle),\qquad O=II+XX-YY+ZZ",
                    size=36,
                )
            ],
            ask=numeric(
                "¿Cuánto vale $\\langle O\\rangle$?",
                4,
                "Correcto: para el estado de Bell, $\\langle XX\\rangle=1$, $\\langle YY\\rangle=-1$ y $\\langle ZZ\\rangle=1$: $1+1-(-1)+1=4$.",
                tol=0.001,
                hint="En el estado de Bell $|\\Phi^+\\rangle$, $\\langle YY\\rangle=-1$.",
            ),
        ),
        beat(
            "precision_pred",
            ("", "Antes de ejecutar"),
            """Por defecto, la Estimator de referencia hace un cálculo exacto. Pero un experimento real usa un número finito de disparos, y eso deja un error estadístico.
             [[exacto]]Los valores exactos eran cuatro, tres coma siete tres y dos. [[apuesta]]Apuesta: si pedimos una precisión de cero coma cero cinco, ¿cómo serán los tres valores?""",
            [
                Table(
                    ["θ", "exacto"], [["0", "4"], ["π/6", "3.73"], ["π/2", "2"]], id="t", size=28
                ),
                T("`precision=0.05`", "note"),
            ],
            [],
            ask=predict(
                "Con `precision=0.05`, ¿cómo serán los tres valores?",
                [
                    "idénticos a los exactos: 4, 3.73 y 2",
                    "cerca de los exactos, pero distintos: el error será del orden de 0.05",
                    "mucho más lejos cuanto mayor sea θ",
                    "todos cero",
                ],
                "Anotado. Veamos qué devuelve.",
            ),
        ),
        beat(
            "precision",
            ("", "Simular el ruido de disparo"),
            """[[prec]]Con el argumento precision introduces el ruido de muestreo que tendría un experimento real: el error estadístico por usar un número finito de disparos.
             [[pub]]La precisión se fija en run, para todos los PUBs o PUB por PUB. [[res]]Con cero coma cero cinco, los valores ya no son exactos: cuatro coma cero dos, tres coma setenta y siete, dos coma cero dos. Si apostaste por la opción b, acertaste: se parecen a los exactos, con errores de unas pocas centésimas.""",
            [
                Code(
                    """estimator = StatevectorEstimator(seed=1)
noisy = estimator.run([(circuit, observable, parameter_values)], precision=0.05).result()
print(noisy[0].data.evs)""",
                    id="c",
                ),
                Out("[4.01727921 3.77313171 2.01652185]", id="o", hidden=True, check=True),
            ],
            [A("hl", "c", at="prec", lines=[2]), A("show", "o", at="res")],
        ),
        beat(
            "sampler",
            ("", "StatevectorSampler"),
            """Ahora Sampler. El circuito debe incluir mediciones. [[varios]]Puedes enviar varios PUBs a la vez y cada uno tiene su resultado. [[bits]]get bitstrings devuelve las cadenas en el orden en que se midieron; get counts, el recuento.
             [[shots]]Los disparos se fijan con shots para todos, [[pub]]o por PUB, como tercer elemento de la tupla. El None hace de marcador porque no hay parámetros.""",
            [
                Code(
                    """from qiskit.primitives import StatevectorSampler

circuit = QuantumCircuit(2)
circuit.h(0)
circuit.cx(0, 1)
circuit.measure_all()
sampler = StatevectorSampler(seed=5)
result = sampler.run([circuit, circuit]).result()
data = result[1].data
print(len(data.meas.get_bitstrings()), data.meas.get_counts())
sampler.run([circuit, circuit], shots=128)
sampler.run([(circuit, None, 123), (circuit, None, 456)])""",
                    id="c",
                    size=22,
                ),
                Out("1024 {'11': 489, '00': 535}", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="varios", lines=[8]),
                A("hl", "c", at="bits", range="9-10"),
                A("show", "o", at="bits", t=1.5),
                A("hl", "c", at="shots", lines=[11]),
                A("hl", "c", at="pub", lines=[12]),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Sobre los disparos.""",
            [
                Code(
                    "sampler.run([(qc1, None, 100), (qc2, None, 300)], shots=50)", setup=SHOTS_SETUP
                )
            ],
            ask=choice(
                "¿Cuántos disparos recibe `qc2`?",
                ["50", "300", "100"],
                1,
                "Correcto: lo que especificas dentro del PUB tiene prioridad sobre el `shots` global.",
                wrong=["El valor del PUB gana al global.", None, "100 es el del primer PUB."],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            "Ahora te toca a ti. [[n1]]Primero apuestas los valores esperados exactos de la lección y los comparas con lo que calcula Estimator. [[n2]]Después ajustas la precisión para que el error de muestreo sea pequeño, pero no cero. [[n3]]Y por último escribes una función que estima una probabilidad con varias cantidades de disparos, un PUB por cada una, en una sola llamada a run.",
            [
                Exercise(
                    "p4-simular-exacto/valores-exactos",
                    "Este código calcula con `StatevectorEstimator` el valor esperado exacto del observable $II+XX-YY+ZZ$ para tres valores de `theta`. Apuesta en `prediccion` una lista con los tres valores y compruébala después.",
                    level=1,
                    needs="qiskit",
                    id="e1",
                    hidden=True,
                    hints=[
                        "Con `theta = 0` el circuito prepara un estado conocido; empieza por ahí.",
                        "Cada término del observable vale +1 o -1 en los estados de Bell; con otros `theta`, el estado cambia y algunos términos dejan de ser exactos.",
                        "La lista tiene tres números, uno por cada valor de `theta`, en el orden de `valores`.",
                    ],
                ),
                Exercise(
                    "p4-simular-exacto/precision",
                    "Cambia **solo** `precision` para que el error máximo de `ruidoso` frente a `exacto` sea menor que 0.02, pero no cero: sigue siendo una simulación con ruido de muestreo.",
                    level=2,
                    needs="qiskit",
                    id="e2",
                    hidden=True,
                    hints=[
                        "`precision` es la desviación estándar del error estadístico que añade la simulación.",
                        "Un valor menor da menos error; un valor de cero lo quita del todo.",
                        "Prueba con un número de la forma `0.00…`, mucho menor que 0.5.",
                    ],
                ),
                Exercise(
                    "p4-simular-exacto/cuatro-pubs",
                    "Escribe `errores_por_disparos(sampler, disparos)`: `sampler` es una primitiva Sampler y `disparos` una lista de cantidades de disparos. Estima $P(1)$ del circuito `qubit` con **una sola llamada a `run`**, con un PUB `(qubit, None, n)` por cada cantidad `n` de `disparos`. Devuelve la lista con la diferencia absoluta entre cada $P(1)$ estimada y `p1_exacto`, en el mismo orden. Ojo: en un PUB, los disparos son el tercer elemento de la tupla.",
                    level=3,
                    needs="qiskit",
                    id="e3",
                    hidden=True,
                    hints=[
                        "Un PUB es una tupla: el circuito, los valores de los parámetros y los disparos.",
                        "Construye la lista de PUBs antes de llamar a `run` y llámalo una vez; cada resultado conserva el orden de su PUB.",
                        "Con `get_counts()` y `num_shots` de cada resultado calculas la fracción de unos; resta `p1_exacto` y toma el valor absoluto.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda en tu navegador.""",
            [T("Un resultado exacto no es lo que verás en un experimento.", "subtitle")],
            ask=reflect(
                "Si la simulación exacta da el valor perfecto, ¿para qué te serviría simular con ruido de muestreo antes de ir a un QPU?",
                "Si multiplicas por cuatro los disparos, ¿qué crees que le pasa al error? Apuesta primero y compruébalo con tu función `errores_por_disparos`.",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]La simulación clásica tiene un límite exponencial. [[r2]]StatevectorEstimator calcula valores exactos, o con ruido de muestreo usando precision. [[r3]]StatevectorSampler muestrea, con disparos globales o por PUB.
             [[r4]]Y no hace falta transpilar para ellas. Para circuitos más grandes o con ruido, la próxima lección: Qiskit Aer.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["simulate-with-qiskit-sdk-primitives", "debugging-tools"],
    practice=[
        "Barre `theta` de 0 a $2\\pi$ con 50 valores en un solo PUB y grafica $\\langle O\\rangle$.",
        "Compara el tiempo de `StatevectorSampler` para un GHZ de 10, 15 y 20 qubits.",
    ],
)

# ------------------------------------------------------------------ 4.4 Aer y ruido
# Context of the thermal-relaxation fragment: T1 and T2 times in nanoseconds for four qubits and an empty model.
THERMAL_SETUP = """import numpy as np
from qiskit_aer.noise import NoiseModel, thermal_relaxation_error

T1s = np.array([50e3, 80e3, 120e3, 60e3])
T2s = np.array([40e3, 90e3, 100e3, 70e3])
noise_thermal = NoiseModel()"""
s_cierre, a_cierre = resumen(
    [
        "`qiskit_aer.primitives`: mismas interfaces, `backend_options=dict(noise_model=…)`",
        "despolarizante: $(1-p)^m$ estima la supervivencia del estado",
        "`NoiseModel` + `QuantumError` (pauli, depolarizing, thermal…) + `ReadoutError`",
        "`add_all_qubit_quantum_error` · `add_quantum_error` · `NoiseModel.from_backend`",
    ]
)
aer = lesson(
    "p4-aer-ruido",
    "Qiskit Aer y modelos de ruido",
    "Simulación exacta y con ruido con las primitivas de Aer, el canal despolarizante, y cómo construir modelos de ruido a medida.",
    [
        "comparar simulación exacta y ruidosa con las primitivas de Aer",
        "estimar el efecto del ruido despolarizante con $(1-p)^m$",
        "construir modelos de ruido con errores de puertas, de lectura y de relajación",
    ],
    [
        beat(
            "exacto",
            ("", "Exacto con Aer"),
            """Los procesadores reales tienen ruido, así que una simulación exacta no refleja lo que verás en hardware. Qiskit Aer permite simular con ruido, y además es más rápido que las primitivas de referencia.
             [[ej]]Tomamos un efficient su2 de ocho qubits, con todos los ángulos en cero coma uno, y el observable Z en todos los qubits. [[tr]]El circuito se transpila para el AerSimulator.
             [[res]]El valor exacto es cero coma ochenta y ocho siete.
             [[nota]]Las primitivas de Aer implementan la misma interfaz, pero no tienen las opciones de IBM, como resilience level.""",
            [
                Code(
                    """from qiskit.circuit.library import efficient_su2
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import EstimatorV2 as Estimator

n_qubits = 8
circuit = efficient_su2(n_qubits)
observable = SparsePauliOp("Z" * n_qubits)
params = [0.1] * circuit.num_parameters
isa_circuit = generate_preset_pass_manager(3, AerSimulator()).run(circuit)
pub = (isa_circuit, observable, params)
exact_value = float(Estimator().run([pub]).result()[0].data.evs)
print(exact_value)""",
                    id="c",
                    size=22,
                ),
                Out("0.8870140234256602", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="ej", range="7-10"),
                A("hl", "c", at="tr", lines=[11]),
                A("show", "o", at="res"),
                A("hl", "c", at="res", range="12-14"),
            ],
        ),
        beat(
            "ruido_pred",
            ("", "Antes de añadir ruido"),
            """Ahora un modelo de ruido simple: un error despolarizante del dos por ciento en cada CX. En la práctica, las puertas de dos qubits son la fuente de error dominante.
             [[cx]]Este circuito tiene veintiuna CX. [[apuesta]]El valor exacto era cero coma ochenta y ocho siete. Apuesta: ¿qué valor devolverá la Estimator con ruido?""",
            [
                Row(
                    Box("def", "Sin ruido", T("$\\langle Z\\cdots Z\\rangle = 0.887$", "body")),
                    Box(
                        "warn",
                        "Con ruido",
                        T("2 % despolarizante en cada una de las 21 CX", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=26,
                )
            ],
            [A("show", "b", at="cx")],
            ask=predict(
                "¿Qué valor esperas con ruido?",
                [
                    "0.887: un 2 % por puerta no se nota",
                    "entre 0.70 y 0.75",
                    "entre 0.50 y 0.60",
                    "cerca de 0",
                ],
                "Anotado. Veámoslo.",
            ),
        ),
        beat(
            "ruido",
            ("", "Con ruido"),
            """[[est]]El modelo se pasa a la Estimator de Aer en backend options. [[res]]Resultado: cero coma setenta y dos, lejos del valor exacto. Si apostaste por la opción b, acertaste. Un dos por ciento por puerta parece poco, pero se acumula en veintiuna puertas.""",
            [
                Code(
                    """from qiskit_aer.noise import NoiseModel, depolarizing_error

noise_model = NoiseModel()
noise_model.add_all_qubit_quantum_error(depolarizing_error(0.02, 2), ["cx"])
noisy_estimator = Estimator(options=dict(backend_options=dict(noise_model=noise_model)))
print(round(float(noisy_estimator.run([pub]).result()[0].data.evs), 4))""",
                    id="c",
                    size=22,
                ),
                Out("0.7247", id="o", hidden=True, check=True),
                Hist(
                    [["exacto", 0.887], ["con ruido", 0.725]],
                    id="h",
                    ymax=1,
                    h=150,
                    digits=3,
                    hidden=True,
                    color="teal",
                ),
            ],
            [
                A("hl", "c", at="ruido", range="3-4"),
                A("hl", "c", at="est", lines=[5]),
                A("show", "o", at="res"),
                A("show", "h", at="res"),
                A("grow", "h", at="res"),
            ],
        ),
        beat(
            "depol",
            ("", "Una estimación rápida"),
            """¿Por qué tanto? El canal despolarizante con probabilidad p deja el estado intacto con probabilidad uno menos p, y con probabilidad p lo reemplaza por el estado completamente mezclado.
             [[m]]Tras m aplicaciones, la probabilidad de que el estado sobreviva es uno menos p elevado a m. [[cx]]El circuito tiene veintiuna CX, [[val]]así que cero coma noventa y ocho a la veintiuno da cero coma sesenta y cinco: una estimación conservadora de que el estado final sea correcto.""",
            [
                M(r"\mathcal E(\rho)=(1-p)\,\rho+p\,\frac{\mathbb 1}{2^n}", size=44),
                M(
                    r"P_{\text{sobrevive}}\approx(1-p)^m=0.98^{21}\approx0.65",
                    id="m",
                    hidden=True,
                    size=42,
                    color="gold",
                ),
            ],
            [A("show", "m", at="m")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Usa la estimación.""",
            [T("Un circuito tiene 50 CX, cada una con un error despolarizante del 1 %.", "body")],
            ask=numeric(
                "¿Qué probabilidad aproximada de supervivencia esperas? (de 0 a 1)",
                0.605,
                "Correcto: $0.99^{50}\\approx0.605$. Con 100 CX bajaría a ≈0.37.",
                tol=0.02,
                hint="Calcula $(1-0.01)^{50}$.",
            ),
        ),
        beat(
            "modulo",
            ("", "El módulo de ruido de Aer"),
            """Para modelos a medida, el módulo noise de Aer tiene tres clases. [[nm]]NoiseModel guarda el modelo completo. [[qe]]QuantumError describe errores de canal cuántico, que se aplican después de puertas o resets, o antes de mediciones.
             [[re]]Y ReadoutError describe errores clásicos de lectura. [[backend]]El atajo: NoiseModel from backend construye un modelo aproximado con los datos de calibración de un dispositivo.""",
            [
                Row(
                    Box("def", "NoiseModel", T("el modelo completo", "body"), id="a", hidden=True),
                    Box(
                        "def",
                        "QuantumError",
                        T("canal CPTP tras puertas o reset, antes de medir", "body"),
                        id="b",
                        hidden=True,
                    ),
                    Box(
                        "def",
                        "ReadoutError",
                        T("$P(\\text{registrado}\\,|\\,\\text{verdadero})$", "body"),
                        id="c",
                        hidden=True,
                    ),
                    gap=20,
                ),
                Code(
                    """noise_model = NoiseModel.from_backend(FakeSherbrooke())""",
                    id="k",
                    hidden=True,
                    setup="from qiskit_aer.noise import NoiseModel\nfrom qiskit_ibm_runtime.fake_provider import FakeSherbrooke",
                ),
            ],
            [
                A("show", "a", at="nm"),
                A("show", "b", at="qe"),
                A("show", "c", at="re"),
                A("show", "k", at="backend"),
            ],
        ),
        beat(
            "errores",
            ("", "Errores estándar"),
            """Hay funciones para los errores más comunes. [[kraus]]Generales: kraus error, con una lista de matrices de Kraus, mixed unitary error y coherent unitary error.
             [[pauli]]De Pauli: pauli error, con una lista de Paulis y probabilidades, y depolarizing error. [[relax]]Físicos: thermal relaxation error, con las constantes T1 y T2 y la duración de la puerta, y los de amortiguamiento de amplitud y de fase.
             [[comb]]Se combinan con compose, tensor y expand, como los operadores.""",
            [
                Table(
                    ["Función", "Parámetros"],
                    [
                        [
                            "`kraus_error` · `mixed_unitary_error` · `coherent_unitary_error`",
                            "matrices de Kraus / unitarias y probabilidades",
                        ],
                        ["`pauli_error` · `depolarizing_error`", "$[(P, p)]$ · $p$"],
                        ["`reset_error`", "$p_0$, $p_1$"],
                        ["`thermal_relaxation_error`", "$T_1$, $T_2$, tiempo, $p_1$"],
                        [
                            "`amplitude_damping_error` · `phase_damping_error` · `phase_amplitude_damping_error`",
                            "$\\lambda$, $\\gamma$, $p_1$",
                        ],
                    ],
                    id="t",
                    stagger=True,
                    size=21,
                )
            ],
            [
                A("item", "t", at="kraus", i=0),
                A("item", "t", at="pauli", i=1),
                A("item", "t", at="pauli", t=1, i=2),
                A("item", "t", at="relax", i=3),
                A("item", "t", at="relax", t=2, i=4),
            ],
        ),
        beat(
            "combinar",
            ("", "Combinar errores"),
            """Un ejemplo: un error de inversión de bit del cinco por ciento, X con probabilidad cero coma cero cinco, y uno de fase, Z con la misma probabilidad.
             [[comp]]Compuestos, dan cuatro posibilidades: nada, con noventa por ciento; X o Z solos, con cuatro coma setenta y cinco cada uno; y ambos, con cero coma veinticinco.
             [[canal]]Los QuantumError se convierten a canales de Qiskit, como Kraus o SuperOp, y de vuelta. [[ro]]Y un ReadoutError se da como una matriz de probabilidades de asignación: por ejemplo, un cinco por ciento de leer uno cuando era cero, y un diez de leer cero cuando era uno.""",
            [
                Code(
                    """from qiskit_aer.noise import pauli_error, ReadoutError

bit_flip = pauli_error([("X", 0.05), ("I", 0.95)])
phase_flip = pauli_error([("Z", 0.05), ("I", 0.95)])
print(bit_flip.compose(phase_flip).probabilities)
print(ReadoutError([[0.95, 0.05], [0.1, 0.9]]))""",
                    id="c",
                    size=22,
                ),
                Out(
                    """[np.float64(0.0025000000000000005), np.float64(0.0475), np.float64(0.0475), np.float64(0.9025)]
ReadoutError on 1 qubits. Assignment probabilities:
 P(j|0) =  [0.95 0.05]
 P(j|1) =  [0.1 0.9]""",
                    id="o",
                    hidden=True,
                    check=True,
                    size=19,
                ),
            ],
            [
                A("hl", "c", at="comp", lines=[5]),
                A("show", "o", at="comp"),
                A("hl", "c", at="ro", lines=[6]),
            ],
        ),
        beat(
            "anadir",
            ("", "Añadir errores al modelo"),
            """Al añadir un error hay que decir a qué instrucciones y a qué qubits afecta. [[todos]]add all qubit quantum error lo aplica a esa instrucción en cualquier qubit.
             [[algunos]]add quantum error, solo en los qubits indicados; para puertas de dos qubits el orden importa: cero uno no es uno cero.
             [[sim]]Luego, AerSimulator con noise model crea un simulador con ese ruido y con las puertas base del modelo. Hay que transpilar para él.""",
            [
                Code(
                    """from qiskit import QuantumCircuit

noise_bit_flip = NoiseModel()
e1 = pauli_error([("X", 0.05), ("I", 0.95)])
noise_bit_flip.add_all_qubit_quantum_error(pauli_error([("X", 0.03), ("I", 0.97)]), "reset")
noise_bit_flip.add_all_qubit_quantum_error(pauli_error([("X", 0.1), ("I", 0.9)]), "measure")
noise_bit_flip.add_all_qubit_quantum_error(e1, ["u1", "u2", "u3"])
noise_bit_flip.add_all_qubit_quantum_error(e1.tensor(e1), ["cx"])
# solo en el qubit 0:  noise_model.add_quantum_error(error, ["u1", "u2", "u3"], [0])

ghz = QuantumCircuit(4)
ghz.h(0)
for q in range(3):
    ghz.cx(q, q + 1)
ghz.measure_all()
sim = AerSimulator(noise_model=noise_bit_flip, seed_simulator=3)
counts = sim.run(generate_preset_pass_manager(3, backend=sim).run(ghz)).result().get_counts()
print(counts["0000"] + counts["1111"])""",
                    id="c",
                    size=19,
                ),
                Out("481", id="o", hidden=True, check=True),
                T(
                    "ideal: 1024 de 1024 en `0000` o `1111` · con ruido: 481",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="todos", range="5-8"),
                A("hl", "c", at="algunos", lines=[9]),
                A("hl", "c", at="sim", range="16-18"),
                A("show", "o", at="sim", t=2),
                A("show", "n", at="sim", t=3),
            ],
        ),
        beat(
            "termico",
            ("", "Relajación térmica"),
            """Un modelo más realista se basa en la relajación térmica. Cada qubit tiene dos constantes de tiempo: T1, de relajación, y T2, de desfase, con la condición T2 menor o igual que dos T1.
             [[tiempos]]El error de cada instrucción depende de su duración: una puerta virtual como u1 no cuesta nada; medir, que dura un microsegundo, cuesta mucho más.
             [[cx]]Para una puerta de dos qubits, se combina el error de cada qubit con expand, y se añade con add quantum error par por par.""",
            [
                M(r"T_2\le 2\,T_1", size=46),
                Code(
                    """errors_measure = [thermal_relaxation_error(t1, t2, 1000) for t1, t2 in zip(T1s, T2s)]
errors_cx = [[thermal_relaxation_error(t1a, t2a, 300).expand(
                  thermal_relaxation_error(t1b, t2b, 300))
              for t1a, t2a in zip(T1s, T2s)] for t1b, t2b in zip(T1s, T2s)]
for j in range(4):
    noise_thermal.add_quantum_error(errors_measure[j], "measure", [j])
    for k in range(4):
        noise_thermal.add_quantum_error(errors_cx[j][k], "cx", [j, k])""",
                    id="c",
                    hidden=True,
                    setup=THERMAL_SETUP,
                    size=20,
                ),
            ],
            [
                A("show", "c", at="tiempos"),
                A("hl", "c", at="tiempos", lines=[1]),
                A("hl", "c", at="cx", range="2-8"),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Sobre los modelos de ruido.""",
            [
                T(
                    'Añades `depolarizing_error(0.01, 2)` a `"cx"` con `add_quantum_error(..., [0, 1])`.',
                    "body",
                )
            ],
            ask=choice(
                "¿Afecta a una CX con control 1 y objetivo 0?",
                ["sí", "no: el orden de los qubits importa"],
                1,
                "Correcto: `[0, 1]` y `[1, 0]` son entradas distintas. Para cubrir todos los casos usa `add_all_qubit_quantum_error` o añade ambas.",
                wrong=["El error está registrado solo para el par ordenado (0, 1)."],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            "Ahora te toca a ti. [[n1]]Primero apuestas qué fracción de los disparos de un GHZ sigue siendo correcta bajo ruido despolarizante. [[n2]]Después buscas qué probabilidad de error deja cerca de la mitad de los disparos correctos. [[n3]]Y por último escribes la función que construye un error de lectura asimétrico.",
            [
                Exercise(
                    "p4-aer-ruido/ideal-vs-ruidoso",
                    "El GHZ de 6 qubits tiene 5 CX, y cada una lleva un error despolarizante del 2 %. Apuesta en `prediccion` qué fracción de los disparos sigue siendo `000000` o `111111` (un número entre 0 y 1) y compruébala después.",
                    level=1,
                    needs="aer",
                    id="e1",
                    hidden=True,
                    hints=[
                        "El ideal solo da dos cadenas; el ruido de cada CX hace que algunos disparos salgan de ellas.",
                        "La lección estima la supervivencia con $(1-p)^m$: aquí $p=0.02$ y $m=5$.",
                        "Calcula $0.98^5$ y piensa si una estimación así sobrestima o subestima los disparos correctos.",
                    ],
                ),
                Exercise(
                    "p4-aer-ruido/p-a-la-mitad",
                    "Cambia **solo** `p`, la probabilidad despolarizante de cada CX, para que la fracción de disparos correctos de `fraccion` caiga entre 0.55 y 0.65. Después compara con $(1-p)^5$: ¿la estimación es pesimista u optimista?",
                    level=2,
                    needs="aer",
                    id="e2",
                    hidden=True,
                    hints=[
                        "Más ruido en cada CX deja menos disparos correctos.",
                        "Prueba valores de `p` mayores que 0.02 y mira `fraccion` en lo que imprime el programa.",
                        "Un valor entre 0.1 y 0.2 deja la fracción cerca de la mitad.",
                    ],
                ),
                Exercise(
                    "p4-aer-ruido/error-de-lectura",
                    "Completa `modelo_lectura(p01, p10)`: devuelve un `NoiseModel` con un `ReadoutError` en todos los qubits, donde `p01` es la probabilidad de leer 1 cuando el valor verdadero es 0 y `p10` la de leer 0 cuando es 1. Ojo: la matriz de asignación tiene una fila por valor verdadero, y cada fila suma 1. Por ejemplo, con `p01 = 0.05` y `p10 = 0.10`, un qubit en $|1\\rangle$ se lee como `0` el 10 % de las veces.",
                    level=3,
                    needs="aer",
                    id="e3",
                    hidden=True,
                    hints=[
                        "Un `ReadoutError` se da como una matriz de probabilidades de asignación.",
                        "La fila $i$ es lo que se registra cuando el valor verdadero es $i$: la fila 0 reparte entre leer 0 y leer 1.",
                        "Rellena las dos filas con `1 - p01`, `p01`, `p10` y `1 - p10`, y añádelo con `add_all_qubit_readout_error`.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar, conectadas con tu proyecto. Escribe con tus palabras; se guardan en tu navegador.""",
            [T("El ruido se acumula con cada puerta de dos qubits.", "subtitle")],
            ask=reflect(
                "En el ejercicio de la probabilidad a la mitad, la estimación `(1 - p) ** m` salió más pesimista que la simulación. ¿Por qué crees que subestima la fracción de disparos correctos?",
                "En tu proyecto Ising, cada paso de Trotter añade CX. ¿Cómo esperas que cambie la curva de magnetización ruidosa a medida que avanza el tiempo simulado?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Las primitivas de Aer aceptan un modelo de ruido en backend options. [[r2]]Uno menos p a la m da una idea rápida del daño. [[r3]]NoiseModel, QuantumError y ReadoutError construyen modelos a medida.
             [[r4]]Y from backend copia el ruido de un dispositivo real.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["simulate-with-qiskit-aer", "build-noise-models"],
    practice=[
        "Varía la probabilidad despolarizante de 0 a 5 % y grafica el valor esperado ruidoso frente a $(1-p)^{21}$ por el valor exacto.",
        "Construye el modelo térmico completo de la guía original y compara sus conteos del GHZ con los del modelo de inversión de bit.",
    ],
)

# ------------------------------------------------------------------ 4.5 Estabilizadores
s_cierre, a_cierre = resumen(
    [
        "Clifford = H, S, CX, medición (y rotaciones de múltiplos de π/2)",
        "se simulan eficientemente: cientos o miles de qubits",
        '`method="stabilizer"` en Aer · solo ruido de Pauli',
        "sirven para verificar hardware y en corrección de errores",
    ]
)
clifford = lesson(
    "p4-estabilizadores",
    "Simular circuitos de Clifford",
    "Qué son los circuitos de estabilizadores, por qué se simulan eficientemente y cómo usarlos con Aer, incluso con 500 qubits y ruido de Pauli.",
    [
        "reconocer un circuito de Clifford",
        "simular circuitos de cientos de qubits con el método `stabilizer`",
        "saber qué ruido admite el simulador de estabilizadores",
    ],
    [
        beat(
            "def",
            ("", "Circuitos de estabilizadores"),
            """Los circuitos de estabilizadores, o de Clifford, son una clase restringida que se puede simular eficientemente en una computadora clásica.
             [[puertas]]Una definición: los que solo usan CX, Hadamard, S y mediciones. [[rot]]Con H y S se construyen las rotaciones de Pauli con ángulos múltiplos de pi medios, salvo una fase global, así que también cuentan.
             [[import]]Son centrales en la corrección de errores cuánticos.""",
            [
                Row(
                    Circ(1, [G("h", 0)], id="a"),
                    Circ(1, [G("s", 0)], id="b"),
                    Circ(2, [G("cx", 0, 1)], id="c"),
                    Circ(1, [G("measure", 0)], clbits=1, id="d"),
                    gap=40,
                ),
                M(
                    r"R_{x,y,z}(\theta),\ \ \theta\in\{0,\tfrac\pi2,\pi,\tfrac{3\pi}2\}",
                    id="m",
                    hidden=True,
                    size=40,
                ),
            ],
            [A("show", "m", at="rot")],
        ),
        beat(
            "verificar",
            ("", "Para qué sirven"),
            """Supón que ejecutas un circuito de cien qubits en un computador cuántico. ¿Cómo sabes si se comportó bien? Un circuito así está fuera del alcance de la simulación por fuerza bruta.
             [[cliff]]Pero si lo modificas para que sea de Clifford, puedes simularlo y comparar. [[conf]]Si el hardware reproduce bien la versión de Clifford, ganas confianza en el experimento original.""",
            [
                Flow(
                    [
                        dict(t="circuito de 100 qubits", s="no simulable"),
                        dict(t="versión de Clifford", s="simulable"),
                        dict(t="comparar con el QPU", s="¿se comporta bien?"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="verificar", i=0),
                A("item", "f", at="cliff", i=1),
                A("item", "f", at="conf", i=2),
            ],
        ),
        beat(
            "q500_pred",
            ("", "Antes de simular"),
            """Un efficient su2 de quinientos qubits es imposible de simular en general. Pero tiene parámetros: si todos los ángulos son múltiplos de pi medios, el circuito es de Clifford.
             [[datos]]Lo muestrearemos mil veinticuatro veces. [[apuesta]]Apuesta: entre esas mil veinticuatro cadenas de quinientos bits, ¿cuántas serán distintas?""",
            [
                Table(
                    ["Dato", "Valor"],
                    [["qubits", "500"], ["ángulos", "múltiplos de $\\pi/2$"], ["disparos", "1024"]],
                    id="t",
                    hidden=True,
                    size=28,
                )
            ],
            [A("show", "t", at="datos")],
            ask=predict(
                "¿Cuántas cadenas distintas habrá entre los 1024 disparos?",
                [
                    "2: solo `0…0` y `1…1`",
                    "unas pocas docenas",
                    "1024: todas distintas",
                    "ninguna: el simulador falla",
                ],
                "Anotado. Veamos.",
            ),
        ),
        beat(
            "q500",
            ("", "Quinientos qubits"),
            """[[sampler]]Creamos un Sampler de Aer con el método stabilizer [[tr]]y transpilamos para el simulador en ese modo.
             [[res]]Resultado: mil veinticuatro cadenas de quinientos bits, en unos segundos. Si apostaste por la opción c, acertaste: las mil veinticuatro son distintas. Un estado de Clifford puede tener una distribución enorme, no solo dos cadenas como un GHZ.""",
            [
                Code(
                    """import numpy as np
from qiskit.circuit.library import efficient_su2
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import SamplerV2 as Sampler

circuit = efficient_su2(500)
measured = circuit.copy()
measured.measure_all()
rng = np.random.default_rng(1234)
params = rng.choice([0, np.pi / 2, np.pi, 3 * np.pi / 2], size=circuit.num_parameters)

sampler = Sampler(seed=1, options=dict(backend_options=dict(method="stabilizer")))
pm = generate_preset_pass_manager(1, AerSimulator(method="stabilizer"))
counts = sampler.run([(pm.run(measured), params)]).result()[0].data.meas.get_counts()
print(len(counts), len(next(iter(counts))))""",
                    id="c",
                    size=21,
                ),
                Out("1024 500", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="q500", range="10-11"),
                A("hl", "c", at="sampler", lines=[13]),
                A("hl", "c", at="tr", lines=[14]),
                A("show", "o", at="res"),
            ],
        ),
        beat(
            "ruido",
            ("", "Ruido de Pauli"),
            """El simulador de estabilizadores también admite ruido, pero solo de un tipo: canales de error de Pauli. El despolarizante es uno de ellos, y también se admiten errores de lectura.
             [[ej]]Este modelo añade un dos por ciento de despolarizante a cada CX y un cinco por ciento de inversión en cada bit medido.
             [[no]]En cambio, la relajación térmica no es un canal de Pauli, así que no se puede usar aquí.""",
            [
                Code(
                    """from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError

noise_model = NoiseModel()
noise_model.add_all_qubit_quantum_error(depolarizing_error(0.02, 2), ["cx"])
noise_model.add_all_qubit_readout_error(ReadoutError([[0.95, 0.05], [0.05, 0.95]]))
noisy_sampler = Sampler(options=dict(backend_options=dict(
    method="stabilizer", noise_model=noise_model)))""",
                    id="c",
                    size=22,
                ),
                Row(
                    Box("def", "Sí", T("Pauli, despolarizante, lectura", "body")),
                    Box(
                        "warn",
                        "No",
                        T("relajación térmica, amortiguamiento", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=26,
                ),
            ],
            [A("hl", "c", at="ej", range="3-5"), A("show", "b", at="no")],
        ),
        beat(
            "estimator",
            ("", "Estimator de estabilizadores"),
            """Con Estimator funciona igual. Calculamos el valor esperado de Z en los quinientos qubits.
             [[cero]]Por la estructura especial de los estados de estabilizadores, el resultado casi siempre es cero: cada valor esperado de un Pauli vale más uno, menos uno o cero.""",
            [
                Code(
                    """from qiskit.quantum_info import SparsePauliOp
from qiskit_aer.primitives import EstimatorV2 as Estimator

estimator = Estimator(options=dict(backend_options=dict(method="stabilizer")))
pub = (pm.run(circuit), SparsePauliOp("Z" * 500), params)
print(float(estimator.run([pub]).result()[0].data.evs))""",
                    id="c",
                ),
                Out("0.0", id="o", hidden=True, check=True),
                M(r"\langle P\rangle\in\{-1,0,+1\}", id="m", hidden=True, size=40),
            ],
            [A("show", "o", at="cero"), A("show", "m", at="cero", t=1)],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """¿Es de Clifford?""",
            [Circ(2, [G("h", 0), G("rz", 0, p="π/4"), G("cx", 0, 1)])],
            ask=choice(
                "¿Puedes simularlo con el método `stabilizer`?",
                ["sí", "no: $R_z(\\pi/4)$ (como T) no es de Clifford"],
                1,
                "Correcto: $\\pi/4$ no es múltiplo de $\\pi/2$. Para pocos T existe el método `extended_stabilizer`, aproximado.",
                wrong=["La rotación de π/4 rompe la estructura de Clifford."],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            "Ahora te toca a ti. [[n1]]Primero simulas un GHZ de cien qubits, algo imposible con un vector de estado, y apuestas cuántas cadenas distintas verás. [[n2]]Después arreglas un circuito que el simulador rechaza, cambiando solo el ángulo de una rotación. [[n3]]Y por último escribes la función que redondea los ángulos de un circuito a múltiplos de pi medios, para obtener su versión de Clifford.",
            [
                Exercise(
                    "p4-estabilizadores/ghz-100",
                    'Un vector de estado de 100 qubits no cabe en ninguna memoria, pero el GHZ es de Clifford y `method="stabilizer"` lo simula al instante. Apuesta en `prediccion` cuántas cadenas distintas salen en los 1024 disparos y compruébalo después.',
                    level=1,
                    needs="aer",
                    id="e1",
                    hidden=True,
                    hints=[
                        "En un GHZ, al medir un qubit ya sabes todos los demás.",
                        "Piensa en cuántas cadenas de 100 bits tienen todos sus bits iguales.",
                        "Escribe un entero, el número de claves de `conteos_ghz`.",
                    ],
                ),
                Exercise(
                    "p4-estabilizadores/rz-de-clifford",
                    "Este circuito lleva una rotación $R_z$ con un ángulo que no es de Clifford, y el simulador de estabilizadores la rechaza. Corrige **solo el ángulo** para que corra. La rotación debe seguir en el circuito.",
                    level=2,
                    needs="aer",
                    id="e2",
                    hidden=True,
                    kind="fix",
                    hints=[
                        "El método `stabilizer` solo acepta rotaciones que son puertas de Clifford.",
                        "Las rotaciones $R_z$ de Clifford son las de ángulos que son múltiplos de $\\pi/2$.",
                        "El ángulo de `angulo` está entre dos múltiplos de $\\pi/2$; elige uno.",
                    ],
                ),
                Exercise(
                    "p4-estabilizadores/a-clifford",
                    "Escribe `a_clifford(params)`: recibe una lista o un arreglo de ángulos y devuelve un arreglo de la misma forma con cada ángulo redondeado al múltiplo de $\\pi/2$ **más cercano**, no hacia abajo. Debe servir también con ángulos negativos o mayores que $2\\pi$. Por ejemplo, `a_clifford([0.1, 2.0, 4.0])` devuelve $[0, \\pi/2, 3\\pi/2]$.",
                    level=3,
                    needs="aer",
                    id="e3",
                    hidden=True,
                    hints=[
                        "Redondear a un múltiplo de $\\pi/2$ es redondear cuántos $\\pi/2$ caben en el ángulo.",
                        "Divide entre $\\pi/2$, redondea al entero más cercano y vuelve a multiplicar.",
                        "NumPy redondea un arreglo entero de una vez con `np.rint`.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar. Escribe con tus palabras; se guardan en tu navegador.""",
            [T("Simular una versión no es simular el original.", "subtitle")],
            ask=reflect(
                "¿Por qué una rotación de π/2 se puede simular con quinientos qubits y una de π/4 ya no, con el mismo método?",
                "Tu QPU reproduce bien la versión de Clifford de un circuito de 100 qubits. ¿Qué sabes con eso del circuito original, y qué no?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Los circuitos de Clifford usan H, S, CX y mediciones. [[r2]]Se simulan eficientemente, con cientos de qubits. [[r3]]En Aer se piden con method igual a stabilizer, y solo admiten ruido de Pauli.
             [[r4]]Y son una gran herramienta para verificar hardware.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["simulate-stabilizer-circuits"],
    practice=[
        "Simula un GHZ de 1000 qubits con el método `stabilizer` y verifica que solo aparecen `0…0` y `1…1`.",
        'Añade una puerta T al circuito y prueba `method="extended_stabilizer"`.',
    ],
)

# ------------------------------------------------------------------ 4.6 Local testing
s_cierre, a_cierre = resumen(
    [
        "modo local: `mode=FakeBackend()` o `mode=AerSimulator(...)`",
        "backends falsos = instantáneas de QPUs reales (mapa, puertas, ruido)",
        "`qiskit-ibm-runtime` ≥ 0.50: mitigación del lado del cliente, también en local",
        "simuladores en la nube retirados (15 de mayo de 2024): simula local, ejecuta en hardware",
    ]
)
local = lesson(
    "p4-local-testing",
    "Modo de prueba local y backends falsos",
    "Probar programas de IBM Quantum en tu computadora con backends falsos o Aer, los métodos de simulación, y probar mitigación de errores antes de usar un QPU.",
    [
        "usar el modo de prueba local con backends falsos y con AerSimulator",
        "elegir el método de simulación de Aer adecuado",
        "probar la mitigación de errores localmente con las primitivas del lado del cliente",
    ],
    [
        beat(
            "idea",
            ("", "Probar en local, ejecutar en la nube"),
            """El modo de prueba local permite probar programas escritos para IBM Quantum antes de enviarlos a hardware real. Cuando funcionan, solo cambias el backend.
             [[fake]]Puedes usar backends falsos, de qiskit ibm runtime fake provider, que imitan procesadores reales con instantáneas: mapa de acoplamiento, puertas base y propiedades de los qubits, incluido su ruido.
             [[aer]]O un simulador de Aer, más rápido y flexible, con modelos de ruido propios.
             [[inst]]Conviene tener Qiskit Aer instalado: los backends falsos lo usan por debajo.""",
            [
                Row(
                    Box(
                        "def",
                        "Backends falsos",
                        L(
                            [
                                "instantáneas de QPUs de IBM",
                                "ruido incluido",
                                "probar el transpilador",
                            ],
                            size=26,
                        ),
                        id="a",
                        hidden=True,
                    ),
                    Box(
                        "idea",
                        "AerSimulator",
                        L(["rápido y flexible", "ruido a medida", "varios métodos"], size=26),
                        id="b",
                        hidden=True,
                    ),
                    gap=26,
                )
            ],
            [A("show", "a", at="fake"), A("show", "b", at="aer")],
        ),
        beat(
            "fake",
            ("", "Con un backend falso"),
            """Un ejemplo con FakeManila, un backend falso de cinco qubits. [[cliente]]Desde qiskit ibm runtime cero punto cincuenta, Sampler y Estimator son primitivas del lado del cliente, en los módulos executor sampler y executor estimator.
             [[mode]]Se pasa el backend falso como mode, y una semilla en las opciones del simulador para resultados reproducibles.
             [[res]]Por el ruido aparecen algunos cero uno y uno cero. Fíjate también: por defecto se usan cuatro mil noventa y seis disparos.""",
            [
                Code(
                    """from qiskit.circuit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_sampler import Sampler
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()
fake_manila = FakeManilaV2()
isa_qc = generate_preset_pass_manager(backend=fake_manila, optimization_level=1).run(qc)
sampler = Sampler(mode=fake_manila, options={"simulator": {"seed_simulator": 42}})
print(sampler.run([isa_qc]).result()[0].data.meas.get_counts())""",
                    id="c",
                    size=22,
                ),
                Out(
                    "{'11': 1934, '00': 1904, '10': 138, '01': 120}",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="cliente", lines=[3]),
                A("hl", "c", at="mode", lines=[12]),
                A("show", "o", at="res"),
                A("hl", "c", at="res", lines=[13]),
            ],
        ),
        beat(
            "aer",
            ("", "Con AerSimulator"),
            """Con AerSimulator es igual. [[sesion]]Se puede usar la sintaxis de sesión, aunque en modo local se ignora: no hay sesiones en tu computadora.
             [[ruido]]Para simular con el ruido de un dispositivo real, AerSimulator from backend construye un simulador con su modelo de ruido. Pero ese modelo solo incluye algunos tipos de ruido, así que suele ser menos severo que el hardware.""",
            [
                Code(
                    """from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import Session

aer_sim = AerSimulator()
isa_qc = generate_preset_pass_manager(backend=aer_sim, optimization_level=1).run(qc)
with Session(backend=aer_sim) as session:       # se ignora en local
    result = Sampler(mode=session).run([isa_qc]).result()

noisy_sim = AerSimulator.from_backend(fake_manila)   # o un backend real""",
                    id="c",
                    size=22,
                )
            ],
            [A("hl", "c", at="sesion", range="6-7"), A("hl", "c", at="ruido", lines=[9])],
        ),
        beat(
            "metodos",
            ("", "Métodos de simulación"),
            """AerSimulator tiene varios métodos. [[auto]]automatic elige solo, según el circuito y el ruido. [[sv]]statevector, vector de estado denso; con ruido, cada disparo simula un circuito ruidoso al azar. [[dm]]density matrix, matriz de densidad, ideal para ruido.
             [[stab]]stabilizer para Clifford, y extended stabilizer, aproximado, para Clifford más algunas T. [[mps]]matrix product state, una red tensorial, eficiente si el entrelazamiento es bajo.
             [[otros]]unitary y superop calculan la matriz del circuito, sin mediciones. Y tensor network, solo en GPU.""",
            [
                Table(
                    ["Método", "Para"],
                    [
                        ["`automatic`", "elegir según circuito y ruido (por defecto)"],
                        ["`statevector`", "ideal; con ruido, trayectorias por disparo"],
                        ["`density_matrix`", "circuitos ruidosos"],
                        ["`stabilizer` · `extended_stabilizer`", "Clifford · Clifford + pocas T"],
                        ["`matrix_product_state`", "poco entrelazamiento, muchos qubits"],
                        [
                            "`unitary` · `superop` · `tensor_network`",
                            "matriz del circuito · canal · GPU",
                        ],
                    ],
                    id="t",
                    stagger=True,
                    size=22,
                )
            ],
            [
                A("item", "t", at="auto", i=0),
                A("item", "t", at="sv", i=1),
                A("item", "t", at="dm", i=2),
                A("item", "t", at="stab", i=3),
                A("item", "t", at="mps", i=4),
                A("item", "t", at="otros", i=5),
            ],
        ),
        beat(
            "mitigar_pred",
            ("", "Antes de mitigar"),
            """Una novedad importante: con las primitivas del lado del cliente, la supresión y mitigación de errores ocurren en tu computadora. Antes, con las primitivas del servidor, esas opciones no tenían efecto en modo local.
             [[ej]]Probemos la mitigación de errores de lectura con Estimator sobre FakeManila. El estado de Bell ideal daría Z Z igual a uno.
             [[apuesta]]Apuesta: ¿qué valor saldrá sin mitigación, y cuál con measure mitigation activada?""",
            [
                Circ(2, [G("h", 0), G("cx", 0, 1)], id="q"),
                M(r"\langle ZZ\rangle_{\text{ideal}} = 1", size=40),
            ],
            [],
            ask=predict(
                "¿Qué valores de ⟨ZZ⟩ esperas en FakeManila?",
                [
                    "1.0 en ambos casos: el simulador es exacto",
                    "sin mitigar cerca de 0.87, y mitigado más cerca de 1",
                    "sin mitigar cerca de 0.99, y mitigado cerca de 0.87",
                    "ambos cerca de 0.5",
                ],
                "Anotado. Veamos el código y los números.",
            ),
        ),
        beat(
            "mitigar",
            ("", "Probar la mitigación en local"),
            """[[ej]]Este es el código. Para cada valor de measure mitigation, un Estimator sobre FakeManila.
             [[sin]]Sin mitigación sale alrededor de cero coma ochenta y siete. [[con]]Con measure mitigation activada, cerca de cero coma noventa y nueve. Si apostaste por la opción b, acertaste. Los valores exactos cambian un poco en cada ejecución.
             [[costo]]Ojo: la mitigación añade memoria y tiempo. Para que las pruebas locales sigan siendo manejables, usa backends pequeños, simuladores sin ruido o simulación de Clifford.""",
            [
                Code(
                    """from qiskit.quantum_info import SparsePauliOp
from qiskit_ibm_runtime.executor_estimator import Estimator

bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)
isa = generate_preset_pass_manager(backend=fake_manila, optimization_level=1).run(bell)
obs = SparsePauliOp("ZZ").apply_layout(isa.layout)
for mitigation in (False, True):
    estimator = Estimator(mode=fake_manila)
    estimator.options.resilience.measure_mitigation = mitigation
    print(mitigation, estimator.run([(isa, obs)]).result()[0].data.evs)""",
                    id="c",
                    size=22,
                ),
                Hist(
                    [["sin mitigar", 0.874], ["mitigado", 0.995]],
                    id="h",
                    ymax=1.1,
                    h=140,
                    digits=3,
                    color="teal",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="ej", range="4-8"),
                A("hl", "c", at="sin", range="9-12"),
                A("show", "h", at="sin"),
                A("grow", "h", at="con"),
            ],
        ),
        beat(
            "migrar",
            ("", "Adiós a los simuladores en la nube"),
            """IBM retiró sus simuladores en la nube el quince de mayo de dos mil veinticuatro. [[por]]Las razones: los simuladores dejan de servir alrededor de cincuenta qubits, incluso en supercomputadoras, y ningún modelo de ruido captura toda la dinámica de un QPU real.
             [[hw]]Trabajar con hardware enseña a usar mitigación y supresión, y a adaptar algoritmos al dispositivo. [[cuando]]Los simuladores siguen siendo útiles para desarrollar y probar, y en tu computadora rinden bien. La recomendación: simula en local, ejecuta en hardware.""",
            [
                Table(
                    ["", "Backends falsos", "AerSimulator", "Clifford"],
                    [
                        [
                            "Propósito",
                            "imitar un QPU concreto",
                            "uso general, rápido",
                            "circuitos de Clifford",
                        ],
                        [
                            "Ruido",
                            "el de la instantánea",
                            "propio o de calibración",
                            "ideal (o Pauli)",
                        ],
                        ["Tamaño", "el del QPU imitado", "mayor", "cientos de qubits"],
                        [
                            "Uso típico",
                            "probar transpilación",
                            "desarrollo general",
                            "corrección de errores",
                        ],
                    ],
                    id="t",
                    stagger=True,
                    size=21,
                )
            ],
            [
                A("item", "t", at="por", i=0),
                A("item", "t", at="hw", i=1),
                A("item", "t", at="cuando", i=2),
                A("item", "t", at="cuando", t=2, i=3),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Elige el simulador.""",
            [
                T(
                    "Quieres comprobar cómo transpila y cuánto ruido sufre tu circuito en un QPU concreto de IBM, sin gastar tiempo de hardware.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué usas?",
                [
                    "un backend falso de ese QPU",
                    '`AerSimulator(method="stabilizer")`',
                    "`StatevectorSampler`",
                ],
                0,
                "Correcto: los backends falsos reproducen el mapa, las puertas base y el ruido de la instantánea del QPU.",
                wrong=[
                    None,
                    "El método de Clifford no imita un QPU concreto.",
                    "Es ideal: no tiene ni mapa ni ruido.",
                ],
            ),
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Sobre la mitigación local.""",
            [
                T(
                    "Con `qiskit-ibm-runtime` 0.50, activas `measure_mitigation` en un Estimator con un backend falso.",
                    "body",
                )
            ],
            ask=choice(
                "¿Tiene efecto?",
                [
                    "no: la mitigación solo existe en el servidor",
                    "sí: las primitivas del lado del cliente la aplican localmente",
                ],
                1,
                "Correcto: desde la 0.50, Sampler y Estimator son del lado del cliente, así que puedes probar mitigación antes de usar un QPU.",
                wrong=["Eso era así con las primitivas del servidor, anteriores a la 0.50."],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            "Ahora te toca a ti. [[n1]]Primero apuestas cuántos disparos hace por defecto el Sampler sobre un backend falso, y ejecutas un estado de Bell. [[n2]]Después cambias el backend por un AerSimulator ideal, sin tocar el resto del programa. [[n3]]Y por último completas una función que estima Z Z con y sin mitigación, y compruebas que la mitigada se acerca más al valor ideal.",
            [
                Exercise(
                    "p4-local-testing/bell-fake",
                    "Este código ejecuta un Bell en `FakeManilaV2`, que imita un procesador real de 5 qubits con su ruido. Apuesta en `prediccion` cuántos disparos hace el Sampler cuando no le pides ninguno, y compruébalo después.",
                    level=1,
                    needs="aer",
                    id="e1",
                    hidden=True,
                    hints=[
                        "Si no pides disparos, el Sampler usa los suyos por defecto.",
                        "La suma de los conteos que devuelve es el número de disparos.",
                        "El valor por defecto es una potencia de dos mayor que 1000.",
                    ],
                ),
                Exercise(
                    "p4-local-testing/sin-ruido",
                    "Cambia `backend` por `AerSimulator()` y deja el resto igual: el programa no cambia, solo el backend. Con un simulador ideal ya no deben aparecer `01` ni `10`.",
                    level=2,
                    needs="aer",
                    id="e2",
                    hidden=True,
                    hints=[
                        "`backend` es la única línea que decide dónde se ejecuta el programa.",
                        "El resto del código lee `backend`: el transpilado y el Sampler.",
                        "`AerSimulator()` sin argumentos es un simulador sin ruido.",
                    ],
                ),
                Exercise(
                    "p4-local-testing/mitigacion",
                    "Completa `ev_zz(mitigar)`: estima $\\langle ZZ\\rangle$ del estado de Bell con un `Estimator` sobre `fake_manila`, activando `resilience.measure_mitigation` cuando `mitigar` es verdadero y desactivándolo cuando es falso. Devuelve un `float`. El valor ideal es 1: la versión mitigada debe acercarse más.",
                    level=3,
                    needs="aer",
                    id="e3",
                    hidden=True,
                    hints=[
                        "Las opciones del Estimator se cambian antes de ejecutar.",
                        "La mitigación de errores de lectura está en `estimator.options.resilience`.",
                        "Asigna el argumento `mitigar` a `measure_mitigation` antes de llamar a `run`.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "proyecto",
            ("", "Tu proyecto: la magnetización en el tiempo"),
            """Cierre de la parte con tu proyecto. [[hito]]El hito cuatro responde la pregunta de la cadena de espines con simuladores: cómo evoluciona la magnetización tras encender el campo, exacta frente a una simulación de Aer con ruido.
             Primero recalculas lo que ya tienes, el Hamiltoniano, el circuito de Trotter y el observable, y comparas la curva exacta con la del circuito. Después añades ruido despolarizante a las CX y simulas con Aer. Y por último escribes una función que dice hasta qué instante te puedes fiar de la simulación ruidosa.
             Ese instante te dirá cuántos pasos pedirle al QPU en la parte cinco.""",
            [
                M(r"M(t)=\frac1N\sum_i\langle Z_i\rangle", size=46),
                Mission(
                    "practica/proyecto/hito4.py",
                    [
                        (
                            1,
                            "Recalcula la magnetización exacta y la del circuito de Trotter, sin ruido.",
                        ),
                        (2, "Añade un error despolarizante a cada CX y simula con `AerEstimator`."),
                        (
                            3,
                            "Escribe `tiempo_de_validez`: el primer instante en que el ruido supera una tolerancia.",
                        ),
                    ],
                    title="Proyecto Ising · Hito IV",
                    id="m",
                    hidden=True,
                ),
            ],
            [A("show", "m", at="hito")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para cerrar la parte. Escribe con tus palabras; se guardan en tu navegador.""",
            [T("Simula en local, ejecuta en hardware.", "subtitle")],
            ask=reflect(
                "Con tus palabras: ¿por qué IBM recomienda simular en local y ejecutar en hardware, si un simulador con ruido ya se parece al QPU?",
                "En el hito IV usaste un ruido despolarizante simple. ¿Qué crees que le falta frente al backend falso de un QPU real, y cómo lo comprobarías?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]En modo local pasas un backend falso o un AerSimulator como mode. [[r2]]Los backends falsos imitan QPUs reales. [[r3]]Desde la cero punto cincuenta, la mitigación también se prueba en local.
             [[r4]]Y la recomendación de IBM: simula en local, ejecuta en hardware. Con esto cierra la Parte cuatro; en la cinco, a la nube.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["local-testing-mode", "local-simulators"],
    practice=[
        "Repite la prueba de mitigación con `FakeBelemV2` y un GHZ de 5 qubits midiendo $\\langle Z_0Z_4\\rangle$.",
        'Prueba `AerSimulator(method="matrix_product_state")` con un GHZ de 60 qubits.',
    ],
)

s_cierre, a_cierre = resumen(
    [
        "Estimator da valores esperados; Sampler, cadenas de bits",
        "el error despolarizante de una puerta multiplica la supervivencia: $(1-p)^{n}$",
        "el método `stabilizer` simula circuitos de Clifford con muchos qubits",
        "`tiempo_de_validez` marca hasta cuándo te puedes fiar de una simulación con ruido",
    ]
)
cierre = lesson(
    "p4-cierre",
    "Cierre de la Parte IV: repaso y tiempo de validez",
    "Un repaso corto de la Parte cuatro y una pregunta del proyecto Ising: hasta qué instante una simulación con ruido sigue la curva exacta.",
    [
        "recordar qué primitiva usar, cómo crece el efecto del ruido y cuándo sirve el método `stabilizer`",
        "calcular el primer instante en que una medida se aleja de la referencia más que una tolerancia",
    ],
    [
        beat(
            "repaso1",
            ("", "Repaso: primitivas"),
            """Tres preguntas rápidas de la Parte cuatro, y después una pregunta del proyecto Ising. La primera, sobre las primitivas.""",
            [T("Sampler → cadenas de bits · Estimator → valores esperados", "subtitle")],
            ask=choice(
                "Quieres la magnetización de una cadena de espines en un instante, es decir, el valor esperado de un observable. ¿Qué primitiva usas?",
                ["Estimator", "Sampler"],
                0,
                "Correcto: Estimator devuelve valores esperados directamente.",
                wrong=[None, "Sampler devuelve cadenas de bits, no valores esperados."],
            ),
        ),
        beat(
            "repaso2",
            ("", "Repaso: ruido"),
            """Segunda pregunta, sobre el efecto del ruido.""",
            [T("Cada puerta ruidosa multiplica la supervivencia por $1-p$", "subtitle")],
            ask=numeric(
                "Un circuito tiene 20 CX y cada una se ensucia con probabilidad $p=0.02$. ¿Qué probabilidad aproximada de que ningún error ocurra? (de 0 a 1)",
                0.668,
                "Correcto: $0.98^{20}\\approx0.668$.",
                tol=0.02,
                hint="Calcula $(1-0.02)^{20}$.",
            ),
        ),
        beat(
            "repaso3",
            ("", "Repaso: simulación de Clifford"),
            """Tercera pregunta, sobre qué método de simulación elegir.""",
            [T("H, S y CX son puertas de Clifford", "subtitle")],
            ask=choice(
                "Tu circuito tiene 40 qubits y solo usa H, S y CX, y luego mide. ¿Qué método de `AerSimulator` usas?",
                ["`statevector`", "`stabilizer`", "`density_matrix`"],
                1,
                "Correcto: los circuitos de Clifford se simulan con el formalismo estabilizador sin guardar $2^{40}$ amplitudes.",
                wrong=[
                    "Guardar $2^{40}$ amplitudes no cabe en la memoria de un equipo normal.",
                    None,
                    "La matriz de densidad necesita aún más memoria que el vector de estado.",
                ],
            ),
        ),
        beat(
            "validez",
            ("", "Tu turno"),
            """Ahora la pregunta del proyecto Ising. [[ej]]Simulaste la magnetización con y sin ruido. Para saber cuántos pasos pedirle a un QPU, necesitas el instante en que la versión ruidosa se aleja demasiado de la exacta. [[n]]Escribe esa función.""",
            [
                Exercise(
                    "p4-cierre/tiempo-de-validez",
                    "Escribe `tiempo_de_validez(tiempos, referencia, medida, tol)`: `tiempos`, `referencia` y `medida` son listas de la misma longitud, y `tol` es la tolerancia. Devuelve el primer tiempo en que la diferencia absoluta entre `medida` y `referencia` es mayor que `tol`, o `None` si nunca ocurre. Ojo: la comparación es estricta, y la medida puede quedar por encima o por debajo de la referencia.",
                    level=3,
                    id="e1",
                    hidden=True,
                    hints=[
                        "Recorre los instantes en orden y para en el primero que cumpla la condición.",
                        "Las tres listas avanzan juntas; `zip` las recorre a la vez.",
                        "Compara el valor absoluto de la diferencia con `tol`, devuelve el tiempo dentro del bucle y deja `None` para cuando el bucle termina.",
                    ],
                )
            ],
            [A("show", "e1", at="ej")],
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen de la parte. [[r1]]Estimator da valores esperados; Sampler, cadenas de bits. [[r2]]El error de cada puerta multiplica la supervivencia. [[r3]]El método stabilizer simula circuitos de Clifford grandes.
             [[r4]]Y el tiempo de validez dice hasta cuándo te puedes fiar de una simulación con ruido. Con esto cierras la Parte cuatro; en la siguiente, ejecutar en IBM Quantum.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[],
    practice=[
        "Calcula `tiempo_de_validez` para tolerancias de 0.02, 0.05 y 0.1 sobre la misma curva ruidosa. ¿Cómo cambia el instante?"
    ],
)

LESSONS = [primitivas, pubs, exacta, aer, clifford, local, cierre]
