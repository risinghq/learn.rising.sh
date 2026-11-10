"""Parte III · Transpilación."""

import math

from lib import (
    A,
    Box,
    Circ,
    Code,
    Exercise,
    Flow,
    G,
    Graph,
    Hist,
    L,
    M,
    Out,
    Row,
    Sh,
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

# Toy chip in a T shape (5 qubits) to explain layout and routing.
T5 = dict(
    nodes=[[0, 0], [1, 0], [2, 0], [1, 1], [1, 2]],
    edges=[[0, 1], [1, 2], [1, 3], [3, 4]],
    unit=110,
    r=24,
)
ANILLO12 = dict(
    nodes=[
        [round(2 * math.cos(k * math.pi / 6), 2), round(2 * math.sin(k * math.pi / 6), 2)]
        for k in range(12)
    ],
    edges=[[k, (k + 1) % 12] for k in range(12)],
    unit=60,
    r=16,
)
ETAPAS = [
    dict(t="init", s="puertas de 1 y 2 qubits", color="blue"),
    dict(t="layout", s="virtuales → físicos", color="teal"),
    dict(t="routing", s="insertar SWAP", color="teal"),
    dict(t="translation", s="puertas base", color="violet"),
    dict(t="optimization", s="reducir puertas", color="gold"),
    dict(t="scheduling", s="tiempos y esperas", color="red"),
]

# ------------------------------------------------------------------ 3.1 Por qué transpilar
s_cierre, a_cierre = resumen(
    [
        "transpilar = adaptar a la topología + optimizar contra el ruido",
        "ISA: solo instrucciones del `Target` y respetando el `CouplingMap`",
        "pases → `PassManager` → `StagedPassManager` de 6 etapas",
        "`generate_preset_pass_manager(nivel, backend).run(qc)` o `transpile`",
    ]
)
transpilar = lesson(
    "p3-transpilar",
    "Por qué hay que transpilar",
    "Qué es la transpilación, qué exige un circuito ISA, qué son los pases y pass managers, y las dos formas de transpilar.",
    [
        "explicar qué hace el transpilador y por qué es obligatorio",
        "describir un circuito ISA en términos de `Target` y `CouplingMap`",
        "transpilar con `generate_preset_pass_manager` y con `transpile`",
    ],
    [
        beat(
            "intro",
            ("", "Reescribir para un chip concreto"),
            """Transpilar es reescribir un circuito para que encaje en la topología de un dispositivo concreto, y optimizar sus instrucciones para ejecutarlas en un computador ruidoso.
             [[antes]]Partes de un circuito con tus instrucciones, las que te resulten cómodas. [[despues]]Y terminas con uno que solo usa las instrucciones disponibles en el backend elegido, organizadas para sufrir lo menos posible el ruido.
             [[local]]Esta parte del curso trata de la transpilación local, que puede hacer cualquier usuario. Si solo usas las opciones por defecto del servicio de IBM, verás más en la parte de ruido.""",
            [
                T("Transpilar", "title"),
                Row(
                    Circ(3, [G("h", 0), G("ccx", 0, 1, 2)], id="a", hidden=True),
                    T("→", "title", id="ar", hidden=True),
                    Circ(
                        3,
                        [
                            G("rz", 0, p="π/2"),
                            G("sx", 0),
                            G("cz", 0, 1),
                            G("rz", 2),
                            G("cz", 1, 2),
                            G("sx", 1),
                            G("cz", 0, 1),
                            G("rz", 1),
                            G("cz", 1, 2),
                            G("sx", 2),
                        ],
                        id="b",
                        hidden=True,
                        scale=0.9,
                    ),
                    gap=20,
                ),
            ],
            [
                A("show", "a", at="antes"),
                A("show", "ar", at="despues"),
                A("show", "b", at="despues"),
            ],
        ),
        beat(
            "isa",
            ("", "La arquitectura del conjunto de instrucciones"),
            """El objetivo es un circuito ISA. Un circuito ISA solo contiene instrucciones que el Target del backend admite: [[base]]sus puertas base, mediciones, resets y operaciones de control de flujo.
             [[mapa]]Y respeta la conectividad del hardware, el CouplingMap: aquí, un chip de juguete en forma de T, donde el qubit uno está conectado a tres vecinos y el cuatro solo a uno.
             [[ibm]]Al enviar un trabajo a un backend de IBM, el servicio exige que el circuito sea ISA.""",
            [
                Row(
                    Box(
                        "def",
                        "Target",
                        L(
                            [
                                "puertas base",
                                "medición, reset",
                                "control de flujo",
                                "errores y duraciones",
                            ],
                            size=26,
                        ),
                        id="t",
                        hidden=True,
                    ),
                    Graph(**T5, id="g", hidden=True),
                    gap=40,
                ),
                T(
                    "IBM Quantum solo acepta circuitos ISA",
                    "note",
                    id="n",
                    hidden=True,
                    color="red",
                ),
            ],
            [
                A("show", "t", at="base"),
                A("show", "g", at="mapa"),
                A("hlnode", "g", at="mapa", t=1.5, i=1),
                A("show", "n", at="ibm"),
            ],
        ),
        beat(
            "pases",
            ("", "Pases y pass managers"),
            """El transpilador está pensado para ser modular y extensible. [[pase]]Cada transformación es un pase, por ejemplo, unir puertas de un qubit seguidas en una sola.
             [[pm]]Un PassManager guarda una lista de pases y los aplica en orden: la salida de uno es la entrada del siguiente. [[spm]]Y un StagedPassManager organiza varios pass managers en etapas.
             [[orden]]Qué pases se encadenan, y en qué orden, cambia muchísimo el resultado final.""",
            [
                Flow(
                    [
                        dict(t="pase", s="una transformación"),
                        dict(t="PassManager", s="lista de pases"),
                        dict(t="StagedPassManager", s="etapas de pass managers"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="pase", i=0),
                A("item", "f", at="pm", i=1),
                A("item", "f", at="spm", i=2),
                A("step", "f", at="orden", i=[0, 1, 2]),
            ],
        ),
        beat(
            "etapas",
            ("", "Seis etapas"),
            """El transpilador prediseñado de Qiskit tiene seis etapas. [[init]]Init: prepara el circuito, por ejemplo convirtiendo puertas de tres o más qubits en puertas de uno y dos.
             [[lay]]Layout: asigna cada qubit virtual de tu circuito a un qubit físico del chip. [[rou]]Routing: inserta SWAP para que las puertas de dos qubits caigan entre vecinos.
             [[tra]]Translation: traduce a las puertas base. [[opt]]Optimization: busca descomposiciones más eficientes. [[sch]]Y scheduling: tiene en cuenta los tiempos de espera de cada qubit.""",
            [Flow(ETAPAS, id="f", stagger=True, numbered=True)],
            [
                A("item", "f", at=m, i=k)
                for k, m in enumerate(["init", "lay", "rou", "tra", "opt", "sch"])
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Una pregunta sobre las etapas.""",
            [Graph(**T5, nodeLabels={0: "a", 4: "b"})],
            ask=choice(
                "Tu circuito tiene una CX entre los qubits que el layout colocó en los físicos 0 y 4. ¿Qué etapa la hace posible?",
                ["init", "routing", "translation", "scheduling"],
                1,
                "Correcto: 0 y 4 no son vecinos, así que el routing inserta SWAP para acercarlos (0–1–3–4).",
                wrong=[
                    "Init solo prepara puertas de 1 y 2 qubits.",
                    None,
                    "Translation cambia las puertas de base, no la conectividad.",
                    "Scheduling se ocupa de tiempos, no de conectividad.",
                ],
            ),
        ),
        beat(
            "predice",
            ("", "Antes de ejecutar"),
            """Vamos a transpilar el circuito del principio, una Hadamard y una Toffoli, para FakeFez, un simulador con las puertas base de un chip de IBM. [[apuesta]]Antes de verlo, apuesta: ¿qué puertas quedan en el resultado?""",
            [Circ(3, [G("h", 0), G("ccx", 0, 1, 2)])],
            ask=predict(
                "Tras transpilar para `FakeFez`, ¿qué tipos de puerta aparecen en el circuito?",
                [
                    "`h` y `ccx`, las mismas",
                    "`cx`, `rz` y `sx`",
                    "`cz`, `rz` y `sx`",
                    "`ecr`, `rz` y `sx`",
                ],
                "Anotado. Ahora lo comprobamos ejecutando el código.",
            ),
        ),
        beat(
            "como",
            ("", "Cómo transpilar"),
            """La forma recomendada es crear un pass manager por etapas con generate preset pass manager, que trae valores razonables, y llamar a su método run con el circuito.
             [[nivel]]El único argumento obligatorio es el nivel de optimización: cero, uno, dos o tres. Más alto, circuitos mejores, pero más tiempo de transpilación.
             [[trans]]La alternativa más simple es la función transpile, que por dentro hace exactamente lo mismo. [[custom]]Y si necesitas más, puedes armar tus propios pass managers: un flujo a medida a menudo suprime errores mejor que el de serie.
             [[res]]Ahora el resultado de tu apuesta: solo cz, rz y sx, las puertas base de FakeFez. Si apostaste por la tercera opción, acertaste. La Hadamard y la Toffoli desaparecieron: ninguna es instrucción del chip.""",
            [
                Code(
                    """from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez

qc = QuantumCircuit(3)
qc.h(0)
qc.ccx(0, 1, 2)
backend = FakeFez()

pm = generate_preset_pass_manager(optimization_level=2, backend=backend)
isa = pm.run(qc)

isa2 = transpile(qc, backend, optimization_level=2)
print(sorted(isa.count_ops()))""",
                    id="c",
                    size=23,
                ),
                Out("['cz', 'rz', 'sx']", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="como", range="10-11"),
                A("hl", "c", at="nivel", lines=[10]),
                A("hl", "c", at="trans", lines=[13]),
                A("hl", "c", at="res", lines=[14]),
                A("show", "o", at="res"),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Una pregunta sobre los niveles.""",
            [
                T(
                    "Tienes que transpilar 10 000 circuitos pequeños lo más rápido posible, y la calidad no es crítica.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué nivel eliges?",
                ["0 o 1", "3", "da igual"],
                0,
                "Correcto: niveles bajos transpilan rápido. El nivel 3 gana calidad a cambio de tiempo.",
                wrong=[
                    None,
                    "El nivel 3 es el más lento.",
                    "No da igual: el tiempo de transpilación crece con el nivel.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Primero, escribe la función que transpila el circuito de la lección con un nivel dado, y compara las cz de los cuatro niveles. [[n2]]Después, arregla un pass manager al que le falta el backend, y por eso no produce un circuito ISA.
             [[n3]]Y por último, escribe tú mismo la función que decide si un circuito es ISA, consultando el Target.""",
            [
                Exercise(
                    "p3-transpilar/cz-por-nivel",
                    "Completa `transpilar(circuito, nivel)`: transpila `circuito` para `FakeFez` con ese nivel de optimización y `seed_transpiler=1`, y devuelve el circuito ISA. Después compara cuántas `cz` quedan del nivel 0 al 3.",
                    level=1,
                    id="e1",
                    hidden=True,
                    hints=[
                        "Transpilar es construir el pass manager del nivel pedido para ese chip y ejecutarlo sobre el circuito.",
                        "El pass manager prediseñado vive en `qiskit.transpiler`; se construye con el nivel y el backend, y la semilla fija el resultado del routing.",
                        "`generate_preset_pass_manager` recibe el nivel, `backend=` y `seed_transpiler=`; el circuito transpilado sale de su método `run`.",
                    ],
                ),
                Exercise(
                    "p3-transpilar/pass-manager-completo",
                    "`pass_manager(nivel)` devuelve un pass manager con el nivel y la semilla ya puestos, pero el circuito que produce no es ISA. Arréglalo para que lo sea en los cuatro niveles.",
                    level=2,
                    id="e2",
                    hidden=True,
                    hints=[
                        "Un pass manager solo adapta el circuito a lo que sabe del chip; si no le dices cuál es, no hay puertas base ni conectividad.",
                        "El chip se entrega al construir el pass manager, no al ejecutarlo.",
                        "`generate_preset_pass_manager` acepta el argumento `backend=`.",
                    ],
                ),
                Exercise(
                    "p3-transpilar/es-isa",
                    "Escribe `es_isa(circuito, target)`: devuelve `True` solo si **cada** instrucción de `circuito` está permitida por `target` en los qubits donde está. "
                    "`circuito` es un `QuantumCircuit` cuyos qubits ya son los físicos y `target` es el `Target` del backend. "
                    "Trampa: preguntar solo por el nombre de la puerta no basta, porque una `cz` puede existir en el chip y no entre esos dos qubits; hay que pasar también los qubits.",
                    level=3,
                    id="e3",
                    hidden=True,
                    hints=[
                        "El Target no solo conoce puertas: conoce en qué qubits puede aplicarse cada una.",
                        "Recorre `circuito.data`; cada instrucción trae su operación y sus qubits, y el índice de un qubit sale de `circuito.find_bit`.",
                        "`target.instruction_supported` recibe el nombre de la operación y la tupla de índices de sus qubits.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma, conectadas con tu proyecto.""",
            [T("Un circuito ISA es el contrato entre tú y el chip.", "subtitle")],
            ask=reflect(
                "¿Por qué crees que IBM **exige** circuitos ISA en lugar de transpilarlos por ti en todos los casos?",
                "Tu proyecto Ising usa `rzz`. `FakeFez` no tiene esa puerta. ¿En qué crees que se convertirá y cómo afectará a la profundidad?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Transpilar adapta el circuito a un chip y lo optimiza. [[r2]]El resultado debe ser ISA. [[r3]]Los pases se organizan en pass managers y estos en seis etapas.
             [[r4]]Y lo habitual es generate preset pass manager con un nivel y un backend. En la próxima lección, las seis etapas por dentro.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["transpile"],
    practice=[
        "Transpila el circuito de la lección para `FakeFez` con los niveles 0 a 3 y compara `count_ops()` y `depth()`.",
        "Compara el tiempo de `pm.run(qc)` entre niveles con `time.perf_counter()` para un `efficient_su2(50)`.",
    ],
)

# ------------------------------------------------------------------ 3.2 Etapas
s_cierre, a_cierre = resumen(
    [
        "init: puertas de ≥3 qubits → 1 y 2 · layout: TrivialLayout, VF2Layout, DenseLayout, SabreLayout",
        "routing: SabreSwap, estocástico (SWAP = 3 CX)",
        "translation: a puertas base (CCX → 6 CX) · optimization: depende del nivel",
        "scheduling: solo si lo pides (`asap`, `alap`) · añade `Delay`",
    ]
)
etapas = lesson(
    "p3-etapas",
    "Las seis etapas del transpilador",
    "Init, layout, routing, translation, optimization y scheduling: qué pases usa cada etapa y qué efectos tiene sobre el circuito.",
    [
        "distinguir qubits virtuales y físicos, y las estrategias de layout",
        "explicar por qué el routing es difícil y estocástico",
        "estimar el costo de traducir SWAP y Toffoli a puertas base",
    ],
    [
        beat(
            "init",
            ("", "Init"),
            """La primera etapa hace poco por defecto: valida las instrucciones y traduce las puertas de tres o más qubits a puertas de uno y dos, porque casi todos los algoritmos de layout y routing solo saben trabajar con esas.
             [[propia]]Es el lugar natural para añadir tus propias optimizaciones iniciales, con plugins o pass managers a medida.""",
            [
                Flow(ETAPAS, id="f", numbered=True),
                Row(
                    Circ(3, [G("ccx", 0, 1, 2)], id="a"),
                    T("→", "title"),
                    Circ(
                        3,
                        [
                            G("h", 2),
                            G("cx", 1, 2),
                            G("tdg", 2),
                            G("cx", 0, 2),
                            G("t", 2),
                            G("cx", 1, 2),
                            G("box", 0, 1, 2, label="…"),
                        ],
                        id="b",
                    ),
                    gap=20,
                ),
            ],
            [A("step", "f", at="init", i=0), A("step", "f", at="propia", i=0)],
        ),
        beat(
            "virtual",
            ("", "Layout: virtuales y físicos"),
            """Los qubits de tu circuito son virtuales: entidades abstractas. Para ejecutar, cada uno debe asignarse a un qubit físico del chip, uno a uno. Esa asignación es el layout.
             [[bien]]Elegirla bien es crucial: un buen layout evita SWAP y usa los qubits mejor calibrados. [[ej]]Si tu circuito tiene un qubit central que interactúa con otros tres, conviene ponerlo en el físico uno, que tiene tres vecinos.""",
            [
                Row(
                    Circ(
                        4,
                        [G("cx", 0, 1), G("cx", 0, 2), G("cx", 0, 3)],
                        qlabels=["a", "b", "c", "d"],
                        id="q",
                    ),
                    Graph(**T5, id="g", numbers=False),
                    gap=50,
                ),
                T("cada qubit virtual → un qubit físico", "note", id="n", hidden=True),
            ],
            [
                A("show", "n", at="virtual"),
                A("nodelabel", "g", at="ej", labels={1: "a", 0: "b", 2: "c", 3: "d"}),
                A("hlnode", "g", at="ej", i=1, color="gold"),
                A("hlnode", "g", at="ej", t=0.6, i=[0, 2, 3], color="teal"),
            ],
        ),
        beat(
            "layouts",
            ("", "Estrategias de layout"),
            """Los pass managers prediseñados prueban varias estrategias. Primero buscan un layout perfecto, que no necesite ningún SWAP.
             [[triv]]TrivialLayout asigna el virtual i al físico i. Es el comportamiento histórico, y solo se usa en el nivel uno como primer intento.
             [[vf2]]VF2Layout trata el problema como un isomorfismo de subgrafos, con el algoritmo VF2 más más; si hay varias soluciones, elige la de menor error medio.
             [[heur]]Si no hay layout perfecto, entra la heurística. [[dense]]DenseLayout busca el subgrafo más conectado, y se usa en el nivel uno si hay control de flujo. [[sabre]]SabreLayout parte de un layout aleatorio y repite el algoritmo SabreSwap para mejorarlo.""",
            [
                Table(
                    ["Pase", "Idea", "Cuándo"],
                    [
                        [
                            "`TrivialLayout`",
                            "virtual $i$ → físico $i$",
                            "primer intento del nivel 1",
                        ],
                        [
                            "`VF2Layout`",
                            "isomorfismo de subgrafos (sin SWAP)",
                            "busca layout perfecto",
                        ],
                        ["`DenseLayout`", "subgrafo más conectado", "nivel 1 con control de flujo"],
                        [
                            "`SabreLayout`",
                            "aleatorio + iterar SabreSwap",
                            "si no hay layout perfecto",
                        ],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                )
            ],
            [
                A("item", "t", at="triv", i=0),
                A("item", "t", at="vf2", i=1),
                A("item", "t", at="dense", i=2),
                A("item", "t", at="sabre", i=3),
            ],
        ),
        beat(
            "routing",
            ("", "Routing"),
            """Si dos qubits que deben interactuar no son vecinos, hay que mover sus estados con puertas SWAP hasta que lo sean. Cada SWAP es caro y ruidoso.
             [[np]]Encontrar el mínimo número de SWAP es un problema NP difícil: imposible de resolver exactamente salvo en casos pequeños.
             [[sabre]]Qiskit usa SabreSwap, una heurística estocástica: da buenas soluciones, no necesariamente óptimas, y puede dar resultados distintos en cada ejecución. Por eso mucha gente transpila varias veces y se queda con el mejor.
             [[juntos]]Por eficiencia, layout y routing se calculan juntos por defecto, aunque son lógicamente distintos.""",
            [
                Graph(**T5, id="g"),
                Box(
                    "idea",
                    "Mover estados",
                    T(
                        "CX entre 0 y 4: SWAP(4,3) y luego SWAP(3,1) llevan el estado de 4 al qubit 1, vecino de 0",
                        "body",
                    ),
                    id="b",
                    hidden=True,
                ),
                T(
                    "NP difícil · SabreSwap es estocástico: transpila varias veces y quédate con el mejor",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("hlnode", "g", at="routing", i=[0, 4], color="red"),
                A("hledge", "g", at="routing", t=2, edges=[[3, 4]], color="gold"),
                A("hledge", "g", at="routing", t=3.5, edges=[[1, 3]], color="gold"),
                A("show", "b", at="np"),
                A("show", "n", at="sabre"),
            ],
        ),
        beat(
            "translation",
            ("", "Translation"),
            """Escribes con las puertas que quieras, pero el chip solo sabe hacer unas pocas: su conjunto de puertas base. Esta etapa traduce todo a ellas, lo que casi siempre alarga el circuito.
             [[swap]]Dos casos ilustran el costo. Un SWAP, si no es nativo, cuesta tres CNOT. [[ccx]]Y una Toffoli, de tres qubits, cuesta seis CNOT y varias puertas de un qubit.
             [[moral]]La moraleja: un algoritmo con muchas Toffoli termina en un circuito profundo, muy afectado por el ruido.""",
            [
                Row(
                    Circ(2, [G("swap", 0, 1)], id="a"),
                    T("=", "title"),
                    Circ(2, [G("cx", 0, 1), G("cx", 1, 0), G("cx", 0, 1)], id="b"),
                    gap=22,
                ),
                Code(
                    """from qiskit import QuantumCircuit

qc = QuantumCircuit(3)
qc.ccx(0, 1, 2)
print(qc.decompose().count_ops())""",
                    id="c",
                    hidden=True,
                ),
                Out(
                    "OrderedDict({'cx': 6, 't': 4, 'tdg': 3, 'h': 2})",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [A("show", "c", at="ccx"), A("show", "o", at="ccx", t=1.5)],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Calcula un costo.""",
            [
                T(
                    "El routing insertó 4 SWAP en tu circuito, y el chip no tiene SWAP nativo.",
                    "body",
                )
            ],
            ask=numeric(
                "¿Cuántas puertas de dos qubits añaden esos SWAP?",
                12,
                "Correcto: cada SWAP son 3 CNOT, así que 12. Por eso minimizar SWAP es una de las metas principales.",
                tol=0.001,
            ),
        ),
        beat(
            "optimization",
            ("", "Optimization"),
            """La etapa de optimización pelea contra la profundidad que añadieron el layout, el routing y la traducción, combinando o eliminando puertas. A veces el circuito final es incluso más corto que el original.
             [[n1]]En el nivel uno, combina cadenas de puertas de un qubit y cancela puertas inversas seguidas. [[n2]]En el nivel dos, usa la conmutación para eliminar más puertas.
             [[n3]]Y en el nivel tres, agrupa bloques de dos qubits, calcula su unitaria y la vuelve a sintetizar, además de todo lo anterior.
             [[fin]]Al final comprueba que todo esté en las puertas base.""",
            [
                Table(
                    ["Nivel", "Pases de optimización"],
                    [
                        ["1", "`Optimize1qGatesDecomposition` · cancelación de inversas"],
                        ["2", "`CommutativeCancellation`"],
                        [
                            "3",
                            "`Collect2qBlocks` · `ConsolidateBlocks` · `UnitarySynthesis` + los anteriores",
                        ],
                    ],
                    id="t",
                    stagger=True,
                    size=25,
                )
            ],
            [
                A("item", "t", at="n1", i=0),
                A("item", "t", at="n2", i=1),
                A("item", "t", at="n3", i=2),
            ],
        ),
        beat(
            "apuesta",
            ("", "Antes de ejecutar"),
            """Un ejemplo con números reales: un estado GHZ de quince qubits, con la CNOT siempre desde el qubit cero, sobre un chip donde los qubits están en línea. El circuito original tiene catorce CNOT.
             El qubit cero tiene que interactuar con todos, así que el routing sufre. Apuesta: con el nivel cero, ¿cuántas CNOT tendrá el resultado?""",
            [
                Row(
                    Box(
                        "idea", "Circuito", T("GHZ de 15 qubits · 14 CNOT desde el qubit 0", "body")
                    ),
                    Box(
                        "def",
                        "Chip",
                        T("15 qubits en línea: cada uno solo ve a sus 2 vecinos", "body"),
                    ),
                    gap=24,
                )
            ],
            ask=predict(
                "Con el nivel 0, ¿cuántas CNOT tiene el circuito transpilado?",
                ["14, las mismas", "unas 30", "unas 60", "más de 200"],
                "Anotado. Ahora lo medimos.",
            ),
        ),
        beat(
            "ejemplo",
            ("", "Los niveles en acción"),
            """Ejecutemos el mismo ejemplo. [[n0]]Con el nivel cero salen sesenta y dos CNOT: cuatro veces las que escribiste; si apostaste por unas sesenta, acertaste. [[n1]]Con el uno, cincuenta; [[n23]]y con los niveles dos y tres, veintiséis, menos de la mitad.
             [[var]]Como el routing es estocástico, estos números cambian con la semilla. Para resultados reproducibles, fija seed transpiler.""",
            [
                Code(
                    """from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import CouplingMap, generate_preset_pass_manager

backend = GenericBackendV2(15, coupling_map=CouplingMap.from_line(15), seed=1)
ghz = QuantumCircuit(15)
ghz.h(0)
ghz.cx(0, range(1, 15))
for level in range(4):
    pm = generate_preset_pass_manager(level, backend=backend, seed_transpiler=1234)
    print(level, pm.run(ghz).count_ops()["cx"])""",
                    id="c",
                    size=22,
                ),
                Hist(
                    [["nivel 0", 62], ["nivel 1", 50], ["nivel 2", 26], ["nivel 3", 26]],
                    id="h",
                    h=170,
                    color="teal",
                    hidden=True,
                    ylabel="CNOT",
                ),
            ],
            [A("show", "h", at="n0"), A("hl", "c", at="var", lines=[9])],
        ),
        beat(
            "scheduling",
            ("", "Scheduling"),
            """La última etapa solo se ejecuta si la pides, con scheduling method: as soon as possible o as late as possible, abreviados asap y alap.
             [[delays]]Contabiliza los tiempos muertos: inserta instrucciones Delay donde un qubit espera sin hacer nada. Así se sabe cuánto durará el circuito en el backend.
             [[dos]]Funciona en dos partes: un pase de análisis, que anota cuándo empieza cada instrucción, y un pase de relleno, que inserta los retrasos o, en lugar de esperas vacías, secuencias de desacoplamiento dinámico.""",
            [
                Code(
                    """ghz = QuantumCircuit(5)
ghz.h(0)
ghz.cx(0, range(1, 5))
pm = generate_preset_pass_manager(
    optimization_level=3, backend=GenericBackendV2(5, seed=1),
    scheduling_method="asap", seed_transpiler=1234)
print(pm.run(ghz).count_ops())""",
                    id="c",
                ),
                Out(
                    "OrderedDict({'delay': 7, 'cx': 4, 'rz': 2, 'sx': 1})",
                    id="o",
                    hidden=True,
                    check=True,
                ),
                Flow(
                    [
                        dict(t="Análisis", s="`ALAPScheduleAnalysis`"),
                        dict(t="Relleno", s="`PadDelay` o `PadDynamicalDecoupling`"),
                    ],
                    id="f",
                    hidden=True,
                ),
            ],
            [A("show", "o", at="delays"), A("show", "f", at="dos")],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Una pregunta conceptual.""",
            [
                T(
                    "Transpilas el mismo circuito dos veces, sin fijar semilla, y obtienes profundidades distintas.",
                    "body",
                )
            ],
            ask=choice(
                "¿Por qué?",
                [
                    "es un error de Qiskit",
                    "el routing (Sabre) es estocástico",
                    "la traducción a puertas base es aleatoria",
                ],
                1,
                "Correcto: SabreLayout y SabreSwap usan aleatoriedad. Fija `seed_transpiler` para reproducir el resultado.",
                wrong=[
                    "Es el comportamiento esperado.",
                    None,
                    "La traducción es determinista; la aleatoriedad viene del layout y el routing.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Primero, escribe la función que cuenta las CNOT del GHZ de quince qubits en línea para cada nivel. [[n2]]Después, elige tú el layout inicial de un chip en forma de T para que el circuito no necesite ningún SWAP.
             [[n3]]Y por último, escribe una función que transpila varias veces con distintas semillas y devuelve el mejor resultado.""",
            [
                Exercise(
                    "p3-etapas/cx-ghz-linea",
                    "Completa `cx_transpilado(circuito, nivel)`: transpila `circuito` para `chip` con ese nivel y `seed_transpiler=1234`, y devuelve cuántas `cx` tiene el resultado. Después mira cómo cambia la cuenta del nivel 0 al 3 con el GHZ de 15 qubits.",
                    level=1,
                    id="e1",
                    hidden=True,
                    hints=[
                        "Cada nivel de optimización es un pass manager distinto, por eso cambian las cuentas.",
                        "Construye el pass manager con el nivel y el chip; la semilla fija el resultado del routing.",
                        "`generate_preset_pass_manager` recibe `backend=` y `seed_transpiler=`; en el circuito transpilado, `count_ops()` da las cuentas por nombre.",
                    ],
                ),
                Exercise(
                    "p3-etapas/layout-estrella",
                    "Con el nivel 0 el transpilador usa tal cual el `initial_layout` que le des. El chip es la T de la lección y el circuito `estrella` hace una `cx` del qubit virtual 0 a cada uno de los otros tres. Cambia `layout_inicial` para que no haga falta ningún SWAP.",
                    level=2,
                    id="e2",
                    hidden=True,
                    hints=[
                        "Aparece un SWAP cuando una puerta de dos qubits une dos qubits físicos que no son vecinos.",
                        "El qubit virtual 0 participa en las tres `cx`: necesita un qubit físico con tres vecinos. Mira qué nodo de la T los tiene.",
                        "`layout_inicial[i]` es el qubit físico donde va el virtual `i`; los cuatro valores deben ser distintos.",
                    ],
                ),
                Exercise(
                    "p3-etapas/mejor-de-semillas",
                    "Completa `mejor_de(qc, semillas)`: recibe un circuito `qc` y un iterable `semillas`, transpila `qc` con `transpilar(qc, semilla)` para cada semilla y devuelve el circuito transpilado con menos `cx`. "
                    "Trampa: devuelves el circuito, no su cuenta ni la semilla, y `semillas` puede ser un `range` o un generador, que se recorre una sola vez.",
                    level=3,
                    id="e3",
                    hidden=True,
                    hints=[
                        "Cada semilla da un routing distinto: tienes que comparar los resultados, no solo transpilar.",
                        "Recorre `semillas` y guarda en `mejor` el circuito con menos `cx` visto hasta ahora.",
                        "Dentro del bucle, transpila, cuenta las `cx` con `count_ops()` y reemplaza `mejor` si aún está vacío o este circuito tiene menos.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma, conectadas con tu proyecto.""",
            [
                T(
                    "Cada SWAP cuesta tres CNOT; cada intento de transpilación cuesta tiempo.",
                    "subtitle",
                )
            ],
            ask=reflect(
                "Probaste varias semillas. ¿Cuántas te parece que merece la pena probar antes de dejar de buscar, y por qué?",
                "Tu cadena Ising tiene vecinos en línea, y el chip también. ¿Qué layout esperas que encuentre el transpilador, y cuántos SWAP crees que necesitará?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Init prepara y layout elige qubits físicos. [[r2]]Routing inserta SWAP con una heurística estocástica. [[r3]]Translation baja a puertas base y optimization recupera lo perdido, más cuanto mayor el nivel.
             [[r4]]Y scheduling, si lo pides, añade los tiempos de espera.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["transpiler-stages"],
    practice=[
        "Repite el GHZ de 15 qubits en línea con 100 semillas distintas en el nivel 1 y grafica el histograma de `depth()`.",
        "Usa `plot_circuit_layout(isa, backend)` para ver qué qubits físicos eligió el layout.",
    ],
)

# ------------------------------------------------------------------ 3.3 Niveles y parámetros
s_cierre, a_cierre = resumen(
    [
        "nivel 0: caracterizar hardware · 1: ligero (por defecto) · 2: medio · 3: re-síntesis KAK",
        "`approximation_degree` < 1: menos CNOT a cambio de exactitud",
        "`seed_transpiler`, `initial_layout`, `*_method` (plugins)",
        "comparar ajustes con la fidelidad de Hellinger frente a la distribución ideal",
    ]
)
niveles = lesson(
    "p3-niveles",
    "Niveles de optimización y parámetros",
    "Qué hace cada nivel, aproximación, semilla, layout inicial, métodos de etapa, todos los parámetros por defecto y cómo comparar configuraciones.",
    [
        "elegir un nivel de optimización según el objetivo",
        "usar `approximation_degree`, `seed_transpiler` e `initial_layout`",
        "comparar configuraciones con la fidelidad de Hellinger",
    ],
    [
        beat(
            "tabla",
            ("", "Los cuatro niveles"),
            """El nivel de optimización controla cuánto esfuerzo invierte el transpilador. [[n0]]Nivel cero: sin optimización, solo traducción y un layout trivial con los SWAP necesarios. Se usa para caracterizar el hardware, cuando quieres ejecutar exactamente lo que escribiste.
             [[n1]]Nivel uno, ligero: intenta el layout trivial y, si hace falta, VF2 y Sabre; cancela inversas y optimiza puertas de un qubit. Es el valor por defecto.
             [[n2]]Nivel dos, medio: más intentos de layout y routing, sin el trivial, y cancelación por conmutación.
             [[n3]]Nivel tres, alto: aún más esfuerzo, re-síntesis de bloques de dos qubits con la descomposición KAK de Cartan, y pases que rompen la unitariedad, como mover mediciones para evitar SWAP o quitar puertas diagonales antes de medir.""",
            [
                Table(
                    ["Nivel", "Qué hace"],
                    [
                        [
                            "0 · ninguna",
                            "traducción + `TrivialLayout` + SWAP · caracterizar hardware",
                        ],
                        [
                            "1 · ligera",
                            "Trivial → VF2/Sabre · `InverseCancellation` · 1q (**por defecto**)",
                        ],
                        ["2 · media", "más intentos de layout/routing · `CommutativeCancellation`"],
                        [
                            "3 · alta",
                            "re-síntesis KAK de bloques 2q · `OptimizeSwapBeforeMeasure` · `RemoveDiagonalGatesBeforeMeasure`",
                        ],
                    ],
                    id="t",
                    stagger=True,
                    size=23,
                )
            ],
            [
                A("item", "t", at="n0", i=0),
                A("item", "t", at="n1", i=1),
                A("item", "t", at="n2", i=2),
                A("item", "t", at="n3", i=3),
            ],
        ),
        beat(
            "apuesta",
            ("", "Antes de ejecutar"),
            """Como las puertas de dos qubits son la mayor fuente de error, una buena medida de calidad es contarlas. Probemos con una unitaria aleatoria de dos qubits seguida de un SWAP, sobre el backend falso Sherbrooke, cuya puerta de dos qubits es la ECR.
             [[reto]]Un SWAP cuesta tres CNOT, y una unitaria aleatoria de dos qubits, hasta tres. Apuesta: con el nivel tres, ¿cuántas ECR quedan?""",
            [Circ(2, [G("box", 0, 1, label="U"), G("swap", 0, 1)])],
            ask=predict(
                "Con `optimization_level=3` en `FakeSherbrooke`, ¿cuántas `ecr` tiene el resultado?",
                ["1", "3", "6", "9"],
                "Anotado. Veamos qué hace cada nivel.",
            ),
        ),
        beat(
            "accion",
            ("", "Los niveles en acción"),
            """Ejecutemos el código con los cuatro niveles. [[n01]]Con los niveles cero y uno salen seis ECR: la unitaria y el SWAP se traducen por separado, a tres cada uno. [[n23]]Con los niveles dos y tres, solo tres: la unitaria y el SWAP se fusionan en un solo bloque de dos qubits, y cualquier unitaria de dos qubits se puede hacer con tres puertas de entrelazamiento como máximo. Si apostaste por tres, acertaste.
             [[nota]]Subir de nivel no siempre cambia algo, pero aquí sí.""",
            [
                Code(
                    """from qiskit import QuantumCircuit
from qiskit.circuit.library import UnitaryGate
from qiskit.quantum_info import random_unitary
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

UU = random_unitary(4, seed=12345)
qc = QuantumCircuit(2)
qc.append(UnitaryGate(UU), range(2))
qc.swap(0, 1)
backend = FakeSherbrooke()
for level in range(4):
    pm = generate_preset_pass_manager(level, backend=backend, seed_transpiler=12345)
    print(level, pm.run(qc).count_ops()["ecr"])""",
                    id="c",
                    size=22,
                ),
                Out("0 6\n1 6\n2 3\n3 3", id="o", hidden=True, check=True),
            ],
            [A("show", "o", at="n01"), A("hl", "c", at="n01", range="12-14")],
        ),
        beat(
            "aprox",
            ("", "Grado de aproximación"),
            """Se puede ir más allá. approximation degree indica cuánto debe parecerse el circuito al original: uno, el valor por defecto, es exacto; valores menores permiten aproximar.
             [[ej]]Con esta unitaria y cero coma noventa y nueve, el nivel tres usa solo dos ECR. [[fid]]La fidelidad de esa síntesis baja a cero coma noventa y nueve dos: introduces un error pequeño a cambio de una puerta ruidosa menos, que en hardware real puede costar más.
             [[qv]]Esta técnica se usó para aumentar el volumen cuántico de los equipos de IBM.""",
            [
                Code(
                    """pm = generate_preset_pass_manager(
    optimization_level=3, approximation_degree=0.99,
    backend=backend, seed_transpiler=12345)
print(pm.run(qc).count_ops()["ecr"])""",
                    id="c",
                ),
                Out("2", id="o", hidden=True, check=True),
                Table(
                    ["", "ECR", "fidelidad de síntesis"],
                    [["exacto (nivel 3)", "3", "1.000"], ["aproximado (0.99)", "2", "0.992"]],
                    id="t",
                    hidden=True,
                    size=25,
                ),
            ],
            [A("show", "o", at="ej"), A("show", "t", at="fid")],
        ),
        beat(
            "seed",
            ("", "Semilla y layout inicial"),
            """Dos parámetros más. [[seed]]seed transpiler fija la semilla de las partes aleatorias: misma semilla, mismo resultado.
             [[lay]]initial layout fija qué qubits físicos usar al principio. Puede ser un objeto Layout, que asigna cada qubit virtual a un entero, o simplemente una lista: el elemento i es el qubit físico del virtual i.
             [[final]]Ojo: el layout final puede ser distinto del inicial, porque el transpilador puede permutar qubits con SWAP. [[mapa]]Para elegir buenos qubits, plot error map dibuja el chip con sus errores.""",
            [
                Code(
                    """from qiskit.transpiler import Layout

pm = generate_preset_pass_manager(1, backend=backend, initial_layout=[5, 6])
isa = pm.run(qc)
print(isa.layout.initial_index_layout()[:2])""",
                    id="c",
                ),
                Out("[5, 6]", id="o", hidden=True, check=True),
                Code(
                    """from qiskit.visualization import plot_error_map
plot_error_map(backend)      # necesita Graphviz instalado""",
                    id="c2",
                    hidden=True,
                    norun=True,
                ),
            ],
            [
                A("hl", "c", at="seed", lines=[3]),
                A("hl", "c", at="lay", range="3-5"),
                A("show", "o", at="lay", t=2),
                A("show", "c2", at="mapa"),
            ],
        ),
        beat(
            "metodos",
            ("", "Métodos de cada etapa"),
            """Los parámetros que terminan en method eligen qué hace cada etapa. [[lay]]layout method: trivial, dense, sabre o el nombre de un plugin. [[rou]]routing method: basic, lookahead, sabre o none.
             [[tra]]translation method: translator, synthesis, y los de IBM para circuitos dinámicos o puertas fraccionales. [[sch]]scheduling method: asap o alap.
             [[otros]]Además, init method, optimization method y unitary synthesis method aceptan plugins. Para ver los instalados, list stage plugins con el nombre de la etapa.""",
            [
                Code(
                    """from qiskit.transpiler.preset_passmanagers.plugin import list_stage_plugins

print(list_stage_plugins("layout"))
print(list_stage_plugins("routing"))
print(list_stage_plugins("scheduling"))""",
                    id="c",
                ),
                Out(
                    """['default', 'dense', 'sabre', 'trivial']
['basic', 'default', 'lookahead', 'none', 'sabre']
['alap', 'asap', 'default']""",
                    id="o",
                    hidden=True,
                    check=True,
                ),
                T(
                    "translation: `translator`, `synthesis`, `ibm_backend`, `ibm_dynamic_circuits`, `ibm_fractional`…",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [A("show", "o", at="lay"), A("show", "n", at="tra")],
        ),
        beat(
            "todos",
            ("", "Todos los parámetros"),
            """Los parámetros se dividen en dos clases. [[target]]Los que describen el objetivo: backend o target, que ya traen todo, o bien sus piezas sueltas: basis gates, coupling map, timing constraints. Si das backend, no necesitas lo demás; si das algo más, como coupling map, eso tiene prioridad.
             [[como]]Y los que influyen en cómo trabaja el transpilador: los métodos de etapa, initial layout, approximation degree, seed, y hls config para la síntesis de alto nivel.
             [[regla]]Una regla importante: lo que fijas a mano, el transpilador no lo cambia.""",
            [
                Code(
                    """generate_preset_pass_manager(
    optimization_level=1,
    backend=None, target=None,
    basis_gates=None, coupling_map=None,
    initial_layout=None,
    layout_method=None, routing_method=None,
    translation_method=None, scheduling_method=None,
    approximation_degree=1.0,
    seed_transpiler=None,
    unitary_synthesis_method="default",
    unitary_synthesis_plugin_config=None,
    hls_config=None,
    init_method=None, optimization_method=None,
)""",
                    id="c",
                    size=22,
                )
            ],
            [
                A("hl", "c", at="target", range="3-4"),
                A("hl", "c", at="como", range="5-15"),
                A("unhl", "c", at="regla"),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Una pregunta sobre parámetros.""",
            [
                Code("""generate_preset_pass_manager(1, backend=backend,
                             coupling_map=[[0, 1], [1, 2]])""")
            ],
            ask=choice(
                "¿Qué mapa de acoplamiento usa el transpilador?",
                ["el del backend", "la línea 0–1–2 que diste", "ninguno: da error"],
                1,
                "Correcto: un argumento explícito como `coupling_map` sobrescribe lo que trae el backend. Qiskit lo avisa con un `UserWarning`: se pierden las duraciones y los errores del backend.",
                wrong=[
                    "Lo que pasas a mano tiene prioridad sobre el backend.",
                    None,
                    "Es válido combinarlos; el explícito gana.",
                ],
            ),
        ),
        beat(
            "comparar",
            ("", "Comparar configuraciones"),
            """¿Cómo saber qué configuración es mejor? Ejecutando y comparando con el resultado ideal. Tomemos el algoritmo de Grover con un oráculo que marca uno uno uno: idealmente, uno uno uno sale con probabilidad cero coma setenta y ocho.
             [[cz]]Transpilado para el backend falso Torino, el nivel cero necesita veintiuna CZ; el nivel tres, solo doce.
             [[dd]]Añadimos una tercera versión: el nivel tres con desacoplamiento dinámico.
             [[sim]]Simulamos las tres con el modelo de ruido del backend, ocho mil disparos.""",
            [
                Code(
                    """from qiskit.circuit.library import grover_operator, DiagonalGate, XGate
from qiskit.quantum_info import Statevector
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes.scheduling import ALAPScheduleAnalysis, PadDynamicalDecoupling
from qiskit_ibm_runtime.fake_provider import FakeTorino

oracle = DiagonalGate([1] * 7 + [-1])
qc = QuantumCircuit(3)
qc.h([0, 1, 2])
qc = qc.compose(grover_operator(oracle))
ideal = Statevector.from_instruction(qc).probabilities_dict()
qc.measure_all()

backend = FakeTorino()
circuits = [generate_preset_pass_manager(lvl, backend=backend, seed_transpiler=0).run(qc)
            for lvl in [0, 3]]
dd = PassManager([ALAPScheduleAnalysis(target=backend.target),
                  PadDynamicalDecoupling(target=backend.target, dd_sequence=[XGate(), XGate()])])
circuits.append(dd.run(circuits[1]))
print([c.count_ops()["cz"] for c in circuits])""",
                    id="c",
                    size=19,
                ),
                Out("[21, 12, 12]", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="comparar", range="7-11"),
                A("hl", "c", at="cz", range="14-16"),
                A("show", "o", at="cz", t=1.5),
                A("hl", "c", at="dd", range="17-19"),
            ],
        ),
        beat(
            "hellinger",
            ("", "Fidelidad de Hellinger"),
            """Para comparar distribuciones usamos la fidelidad de Hellinger: uno es perfecto. [[n0]]El nivel cero llega a cero coma noventa y dos. [[n3]]El nivel tres, a cero coma noventa y nueve cuatro: menos puertas, menos error.
             [[dd]]Con desacoplamiento dinámico, cero coma noventa y nueve uno: en este simulador no mejora, porque su modelo de ruido no incluye los efectos que el desacoplamiento corrige, como la diafonía entre qubits. En hardware real suele ayudar.
             [[moral]]La moraleja: una misma configuración puede ayudar a un circuito y perjudicar a otro. Revisa siempre los circuitos transpilados antes de gastar tiempo de hardware.""",
            [
                Code(
                    """from qiskit_aer.noise import NoiseModel
from qiskit_aer.primitives import SamplerV2
from qiskit.quantum_info import hellinger_fidelity

sampler = SamplerV2(seed=7, options={"backend_options": {"noise_model": NoiseModel.from_backend(backend)}})
result = sampler.run(circuits, shots=8000).result()
for res in result:
    probs = {k: v / 8000 for k, v in res.data.meas.get_counts().items()}
    print(f"{hellinger_fidelity(probs, ideal):.3f}")""",
                    id="c",
                    size=20,
                ),
                Hist(
                    [["nivel 0", 0.92], ["nivel 3", 0.994], ["nivel 3 + DD", 0.991]],
                    id="h",
                    ymax=1.1,
                    h=150,
                    digits=3,
                    color="teal",
                    hidden=True,
                ),
            ],
            [A("show", "h", at="n0"), A("grow", "h", at="n0")],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Una pregunta sobre aproximación.""",
            [
                T(
                    "Aproximar la síntesis quita una ECR, pero la fidelidad de la síntesis baja a 0,992.",
                    "body",
                )
            ],
            ask=choice(
                "¿Cuándo conviene?",
                [
                    "nunca: siempre hay que ser exacto",
                    "cuando el error de una ECR en el hardware supera al error de aproximación",
                    "solo en simuladores",
                ],
                1,
                "Correcto: si quitar una puerta ruidosa ahorra más error del que introduce la aproximación, el resultado neto mejora.",
                wrong=[
                    "En hardware ruidoso, aproximar puede dar mejores resultados.",
                    None,
                    "En un simulador ideal no tiene sentido aproximar: no hay ruido que ahorrar.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Primero, escribe la función que cuenta las ECR de la unitaria con SWAP en cada nivel. [[n2]]Después, usa el grado de aproximación para quitar una ECR de más.
             [[n3]]Y por último, simula con ruido el algoritmo de Grover y mide cuánta fidelidad gana cada nivel.""",
            [
                Exercise(
                    "p3-niveles/ecr-por-nivel",
                    "Completa `ecr_por_nivel(circuito)`: transpila `circuito` para `FakeSherbrooke` con cada nivel, de 0 a 3 y con `seed_transpiler=12345`, y devuelve una lista con las `ecr` de cada resultado, en ese orden. Después mira en qué nivel baja la cuenta.",
                    level=1,
                    id="e1",
                    hidden=True,
                    hints=[
                        "Hay un pass manager por nivel: repite lo mismo cuatro veces cambiando solo el nivel.",
                        "Recorre `range(4)`; la `ecr` es la puerta de dos qubits de este chip, así que búscala por nombre en las cuentas del circuito transpilado.",
                        "`count_ops()` devuelve un diccionario nombre → cuenta; si la puerta no aparece, la cuenta es 0.",
                    ],
                ),
                Exercise(
                    "p3-niveles/aproximar",
                    "Con el nivel 3, la unitaria con SWAP de este ejercicio sale con 3 `ecr`. Cambia `grado` (el `approximation_degree`) para que salgan 2 o menos. "
                    "El 0,99 de la lección dejaba 2 `ecr` con otra unitaria; con esta no basta, y un grado demasiado bajo aproxima tanto que el circuito deja de parecerse a la unitaria: no bajes de 0,9.",
                    level=2,
                    id="e2",
                    hidden=True,
                    hints=[
                        "`approximation_degree` vale 1.0 cuando la síntesis es exacta; un valor menor deja que el transpilador cambie exactitud por menos puertas.",
                        "Prueba valores entre 1 y 0,9 y mira cuántas `ecr` imprime cada uno.",
                        "Cambia solo `grado`: busca el valor más alto que lleve a 2 `ecr`.",
                    ],
                ),
                Exercise(
                    "p3-niveles/fidelidad",
                    "Completa `fidelidad(circuito, nivel)`: transpila `medido` para `FakePeekskill` con ese `nivel` y `seed_transpiler=0`, simúlalo con `SamplerV2` de Aer, con el ruido `ruido` y `SHOTS` repeticiones, y devuelve la fidelidad de Hellinger entre lo medido y la distribución `ideal`. "
                    "Trampa: `hellinger_fidelity` espera probabilidades y `get_counts()` da conteos; divide cada conteo entre `SHOTS`.",
                    level=3,
                    id="e3",
                    hidden=True,
                    needs="aer",
                    hints=[
                        "Un simulador con ruido muestra cuánto daña cada nivel: más puertas de dos qubits acumulan más ruido.",
                        "Pasa `medido` transpilado a `SamplerV2` de `qiskit_aer.primitives`, con el modelo de ruido en `backend_options`; el registro de `measure_all` se llama `meas`.",
                        "`hellinger_fidelity(p, q)` compara dos diccionarios de probabilidades; los conteos de `get_counts()` hay que dividirlos primero.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma, conectadas con tu proyecto.""",
            [T("Más esfuerzo del transpilador no siempre da un circuito mejor.", "subtitle")],
            ask=reflect(
                "Hoy el nivel 3 fue el mejor en las ECR, pero no siempre lo es. ¿Cómo decidirías qué nivel usar en tu proyecto Ising?",
                "`approximation_degree` cambia exactitud por menos puertas. ¿En qué condiciones del hardware aceptarías un 1 % de error de síntesis?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]El nivel de optimización va de cero, para caracterizar, a tres, con re-síntesis. [[r2]]approximation degree cambia exactitud por menos puertas. [[r3]]seed, initial layout y los métodos de etapa afinan el proceso.
             [[r4]]Y para elegir, compara con la distribución ideal usando la fidelidad de Hellinger.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "set-optimization",
        "common-parameters",
        "defaults-and-configuration-options",
        "circuit-transpilation-settings",
    ],
    practice=[
        "Repite la comparación de Grover con `FakeFez` y con `optimization_level` 1 y 2.",
        "Barre `approximation_degree` de 1.0 a 0.8 para la unitaria aleatoria y grafica el número de ECR.",
    ],
)

# ------------------------------------------------------------------ 3.4 Target
s_cierre, a_cierre = resumen(
    [
        "`Backend` = `Target` + `run()` + `max_circuits` + opciones",
        "`Target`: instrucciones, conectividad, errores y duraciones",
        "mapa de acoplamiento: qubits virtuales → físicos, SWAP si hace falta",
        "`Target.add_instruction(gate, {qargs: InstructionProperties})` para backends propios",
    ]
)
target = lesson(
    "p3-target",
    "Representar un computador cuántico: Target",
    "Qué información necesita el transpilador: Backend y Target, mapa de acoplamiento, instrucciones soportadas, errores, y cómo crear un backend propio.",
    [
        "explicar el papel de `Backend` y `Target` en la transpilación",
        "ver el efecto del mapa de acoplamiento, las puertas base y los errores",
        "construir un `Target` y un `BackendV2` a medida",
    ],
    [
        beat(
            "intro",
            ("", "Backend y Target"),
            """Para producir un circuito ISA, el transpilador necesita saber cómo es el procesador. Esa información vive en dos lugares.
             [[target]]El Target guarda todas las restricciones del dispositivo: sus instrucciones, la conectividad de sus qubits, y la información de tiempos y errores.
             [[backend]]El Backend contiene un Target, más la interfaz para enviar trabajos. [[mas]]Cuanta más información tenga el Target, mejor puede trabajar el transpilador, aunque como muchos algoritmos son estocásticos, no hay garantía de encontrar el mejor circuito.""",
            [
                Row(
                    Box(
                        "def",
                        "Target",
                        L(["instrucciones", "conectividad", "errores y duraciones"], size=27),
                        id="t",
                        hidden=True,
                    ),
                    Box(
                        "idea",
                        "Backend",
                        L(["un `Target`", "`run()`: enviar trabajos", "opciones"], size=27),
                        id="b",
                        hidden=True,
                    ),
                    gap=30,
                )
            ],
            [A("show", "t", at="target"), A("show", "b", at="backend")],
        ),
        beat(
            "anillo",
            ("", "Un anillo en un chip"),
            """El mapa de acoplamiento es un grafo: dice qué qubits están conectados y pueden hacer puertas de dos qubits entre sí. A veces es dirigido, pero el transpilador siempre puede invertir una puerta añadiendo puertas de un qubit.
             [[ej]]Tomemos un circuito efficient su2 de doce qubits, con entrelazamiento circular: cada qubit habla con el siguiente, y el último con el primero. Necesita un anillo. Con el nivel cero, el layout trivial pone los qubits uno, dos, tres... en línea sobre el chip. Apuesta: ¿cuántos SWAP hacen falta?""",
            [Graph(**ANILLO12, id="g")],
            ask=predict(
                "Con el nivel 0 y el mapa de `FakeSherbrooke`, ¿cuántos `swap` inserta el routing?",
                ["0, el chip tiene anillos", "unos 2", "unos 22", "más de 100"],
                "Anotado. Ahora lo medimos con y sin optimización.",
            ),
        ),
        beat(
            "cm",
            ("", "El mapa de acoplamiento"),
            """Ejecutemos el ejemplo. [[ej]]El circuito efficient su2 de doce qubits, con entrelazamiento circular, necesita un anillo. [[n0]]Con el nivel cero y solo el mapa de acoplamiento de Sherbrooke, el layout trivial pone los qubits en línea y hacen falta veintidós SWAP; si apostaste por unos veintidós, acertaste.
             [[n1]]Con el nivel uno, VF2 y Sabre encuentran un layout casi en anillo: solo dos SWAP.""",
            [
                Code(
                    """from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import efficient_su2
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

target = FakeSherbrooke().target
qc = efficient_su2(12, entanglement="circular", reps=1)
coupling_map = target.build_coupling_map()
for level in (0, 1):
    pm = generate_preset_pass_manager(level, coupling_map=coupling_map, seed_transpiler=12345)
    print(level, pm.run(qc).count_ops()["swap"])""",
                    id="c",
                    size=23,
                ),
                Out("0 22\n1 2", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="ej", lines=[7]),
                A("show", "o", at="n0"),
                A("hl", "c", at="n0", range="8-11"),
            ],
        ),
        beat(
            "base",
            ("", "Instrucciones soportadas"),
            """Cada computador soporta un conjunto limitado de instrucciones, que debe ser universal: cualquier operación se puede descomponer en ellas. El pase BasisTranslator hace la traducción.
             [[sb]]Sherbrooke usa rz, sx y x en un qubit, y ECR, la puerta de resonancia cruzada con eco, en dos qubits: es la parte que entrelaza dentro de una CX. [[mas]]También admite delay, medición, reset y control de flujo.
             [[otros]]Otros procesadores usan CZ, como Fez, Torino o Heron. Puedes pasar basis gates como argumento, y las CX se descompondrán en ECR más puertas de un qubit.""",
            [
                Code("""print(sorted(target.operation_names))""", id="c"),
                Out(
                    "['delay', 'ecr', 'for_loop', 'id', 'if_else', 'measure', 'reset', 'rz', 'switch_case', 'sx', 'x']",
                    id="o",
                    hidden=True,
                    check=True,
                ),
                Row(
                    Box("def", "Eagle (Sherbrooke)", T("1q: `rz` `sx` `x` · 2q: `ecr`", "body")),
                    Box("def", "Heron (Fez, Torino)", T("1q: `rz` `sx` `x` · 2q: `cz`", "body")),
                    id="r",
                    hidden=True,
                    gap=26,
                ),
            ],
            [A("show", "o", at="sb"), A("show", "r", at="otros")],
        ),
        beat(
            "errores",
            ("", "Errores del dispositivo"),
            """El Target también guarda las propiedades de cada instrucción en cada qubit o par de qubits. [[ecr]]Para la ECR entre los qubits uno y cero: dura unos quinientos treinta y tres nanosegundos y tiene un error de cero coma siete por ciento. La ECR es direccional: uno cero no es lo mismo que cero uno.
             [[uso]]Con esa información, el pase VF2PostLayout elige los qubits físicos con menos error.
             [[from]]Puedes construir un Target desde una configuración, con from configuration, y copiarle los errores de otro.""",
            [
                Code("""print(target["ecr"][(1, 0)])""", id="c"),
                Out(
                    "InstructionProperties(duration=5.333333333333332e-07, error=0.007494257741828603)",
                    id="o",
                    hidden=True,
                    check=True,
                ),
                Code(
                    """from qiskit.transpiler import Target
err_targ = Target.from_configuration(
    basis_gates=basis_gates, coupling_map=coupling_map,
    num_qubits=target.num_qubits)
for i, (op, qargs) in enumerate(target.instructions):
    if op.name in basis_gates:
        err_targ[op.name][qargs] = target.instruction_properties(i)""",
                    id="c2",
                    hidden=True,
                    setup='basis_gates = ["rz", "sx", "x", "ecr"]',
                    size=22,
                ),
            ],
            [A("show", "o", at="ecr"), A("show", "c2", at="from")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Una pregunta sobre el Target.""",
            [T("Solo le das al transpilador el `coupling_map`, sin puertas base.", "body")],
            ask=choice(
                "¿Es el resultado un circuito ISA para Sherbrooke?",
                [
                    "sí",
                    "no: respeta la conectividad pero puede tener puertas que el chip no ejecuta",
                    "no: ni siquiera respeta la conectividad",
                ],
                1,
                "Correcto: sin puertas base no hay traducción; quedan CX, H, RY… que Sherbrooke no ejecuta. Lo más simple es pasar `backend` o `target`.",
                wrong=[
                    "Faltan las puertas base para que sea ISA.",
                    None,
                    "La conectividad sí se respeta: para eso sirve el mapa.",
                ],
            ),
        ),
        beat(
            "propio",
            ("", "Un backend propio"),
            """Qiskit no depende del fabricante: cualquiera puede describir su propio dispositivo. Las piezas son tres. [[prov]]Un Provider, que entrega objetos backend y se ocupa de credenciales.
             [[backend]]Un BackendV2, con cuatro partes: un Target, max circuits, el máximo de circuitos por trabajo, un método run, y unas opciones por defecto.
             [[target]]Y el Target, que se llena con add instruction: para cada puerta, un diccionario de los qubits donde está disponible, con su error y su duración.
             [[res]]Una CX entre los qubits cero y dos, que no son vecinos en esta cadena: el transpilador los coloca en dos qubits contiguos, así que no hacen falta SWAP, y traduce la CX a una CZ y puertas de un qubit.
             La X está en el Target, pero el transpilador solo la usa cuando una secuencia de puertas de un qubit equivale, salvo rotaciones Z, a una X; aquí ninguna lo hace, y por eso no aparece. Todo salió de la información del Target.""",
            [
                Code(
                    """from qiskit.providers import BackendV2, Options
from qiskit.transpiler import Target, InstructionProperties
from qiskit.circuit.library import XGate, SXGate, RZGate, CZGate
from qiskit.circuit import Measure, Parameter

class MiBackend(BackendV2):
    def __init__(self):
        super().__init__(name="mi_backend")
        self._target = Target("cadena de 3", num_qubits=3)
        self._target.add_instruction(RZGate(Parameter("t")),
            {(q,): InstructionProperties(error=0.0, duration=0.0) for q in range(3)})
        for gate in (XGate(), SXGate(), Measure()):
            self._target.add_instruction(gate, {(q,): None for q in range(3)})
        self._target.add_instruction(CZGate(),
            {(0, 1): InstructionProperties(error=5e-3), (1, 2): InstructionProperties(error=5e-3)})

    @property
    def target(self): return self._target
    @property
    def max_circuits(self): return None
    @classmethod
    def _default_options(cls): return Options(shots=1024)
    def run(self, circuit, **kwargs): raise NotImplementedError

qc = QuantumCircuit(3)
qc.h(0)
qc.cx(0, 2)
print(sorted(transpile(qc, MiBackend()).count_ops()))""",
                    id="c",
                    size=17,
                ),
                Out("['cz', 'rz', 'sx']", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="prov", range="6-8"),
                A("hl", "c", at="backend", range="17-24"),
                A("hl", "c", at="target", range="9-15"),
                A("hl", "c", at="res", range="26-29"),
                A("show", "o", at="res"),
            ],
        ),
        beat(
            "multichip",
            ("", "Un backend de varios chips"),
            """La guía original construye un backend más ambicioso: tres chips, cada uno con conectividad heavy hex, generada con la biblioteca rustworkx.
             [[dentro]]Dentro de cada chip, la puerta de dos qubits es CZ; [[entre]]entre chips, ECR, en un solo enlace.
             [[ghz]]Al transpilar un GHZ de cincuenta qubits, el resultado mezcla las dos puertas: doscientas cuatro CZ y ocho ECR, con muchos SWAP para cruzar entre chips.
             [[vis]]plot gate map y plot circuit layout dibujan estos dispositivos y qué qubits usó el circuito. Y con rustworkx puedes inventar cualquier geometría, como un toro de veinte por veinte.""",
            [
                Graph(
                    [
                        [0, 0],
                        [1, 0],
                        [2, 0],
                        [0, 1],
                        [2, 1],
                        [0, 2],
                        [1, 2],
                        [2, 2],
                        [4, 0],
                        [5, 0],
                        [6, 0],
                        [4, 1],
                        [6, 1],
                        [4, 2],
                        [5, 2],
                        [6, 2],
                    ],
                    [
                        [0, 1],
                        [1, 2],
                        [0, 3],
                        [2, 4],
                        [3, 5],
                        [4, 7],
                        [5, 6],
                        [6, 7],
                        [8, 9],
                        [9, 10],
                        [8, 11],
                        [10, 12],
                        [11, 13],
                        [12, 15],
                        [13, 14],
                        [14, 15],
                        [4, 11],
                    ],
                    unit=70,
                    numbers=False,
                    id="g",
                ),
                Table(
                    ["", "antes", "después"],
                    [["CX / CZ", "49", "204 CZ"], ["ECR (entre chips)", "—", "8"]],
                    id="t",
                    hidden=True,
                    size=25,
                ),
            ],
            [A("hledge", "g", at="entre", edges=[[4, 11]], color="red"), A("show", "t", at="ghz")],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Una pregunta sobre backends.""",
            [T("Un backend es un `Target` más la forma de ejecutar circuitos.", "body")],
            ask=choice(
                "¿Qué parte del backend no puede cambiar el circuito transpilado?",
                ["el `Target`", "el método `run`", "las puertas que declara el `Target`"],
                1,
                "Correcto: `run` solo envía trabajos al dispositivo; el transpilador lee el `Target`, no `run`.",
                wrong=[
                    "El `Target` es justo lo que lee el transpilador: si cambia, cambia el resultado.",
                    None,
                    "Esas puertas son parte del `Target`: cambian el resultado.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Primero, completa el backend de tres qubits de la lección para que traduzca una CX entre los extremos sin SWAP. [[n2]]Después, en un anillo de cuatro qubits, quita del Target el par averiado para que el transpilador lo esquive.
             [[n3]]Y por último, escribe una función que construye un Target para una cadena de cualquier tamaño.""",
            [
                Exercise(
                    "p3-target/mi-backend",
                    "`MiBackend` es la cadena de tres qubits 0-1-2 de la lección: ya tiene `rz`, `sx`, `x` y la medición, pero a `cz` le falta un par. Complétalo y transpila una `cx` entre los qubits 0 y 2: no debe salir ningún `swap`.",
                    level=1,
                    id="e1",
                    hidden=True,
                    hints=[
                        "Un `Target` solo conoce las conexiones que le declares: la cadena 0-1-2 tiene dos enlaces.",
                        "La puerta `CZGate()` se añade con un diccionario cuyas claves son las tuplas de qubits donde existe.",
                        "Cada clave es un par `(a, b)` y su valor, un `InstructionProperties`.",
                    ],
                ),
                Exercise(
                    "p3-target/anillo-averiado",
                    "El anillo de 4 qubits sale de `errores_cz`, que da el error de cada par. La tabla dice que el par (1, 2) es casi perfecto, pero tú sabes que está averiado. Cambia `errores_cz` para que el transpilador nunca use ese par.",
                    level=2,
                    id="e2",
                    hidden=True,
                    hints=[
                        "El transpilador se fía de la tabla: solo deja de usar un par si dejas de ofrecérselo.",
                        "Lo que no está en el `Target` no existe para el transpilador; piensa en qué pares declaras para `cz`.",
                        "El diccionario `errores_cz` tiene una entrada por par.",
                    ],
                ),
                Exercise(
                    "p3-target/cadena-n",
                    "Escribe `cadena(n)`: devuelve un `Target` de `n` qubits con `rz`, `sx`, `x` y `measure` en cada qubit, y `cz` **solo** entre vecinos (0–1, 1–2…). "
                    "`n` es el número de qubits y vale 3 o más. Trampa: una cadena de `n` qubits tiene `n - 1` pares vecinos, no `n`, y la comprobación exige que un GHZ de `n` qubits se transpile sin ningún SWAP.",
                    level=3,
                    id="e3",
                    hidden=True,
                    hints=[
                        "La cadena es un camino: cada qubit se conecta con el siguiente y con nadie más.",
                        "`rz` ya está añadida en todos los qubits; `sx`, `x` y `measure` se añaden igual, y `cz` solo en los pares vecinos.",
                        "Las puertas de un qubit llevan un diccionario con claves `(q,)`; `cz` lleva uno con claves `(a, b)`. El valor de cada clave puede ser `None` o un `InstructionProperties`.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma, conectadas con tu proyecto.""",
            [T("El transpilador solo sabe lo que dice el Target.", "subtitle")],
            ask=reflect(
                "Un qubit de tu chip se vuelve ruidoso a mitad del día. ¿Qué cambiarías en el `Target` para que el transpilador lo evite, y qué perderías?",
                "Tu cadena Ising tiene vecinos en línea. ¿Qué tendría que tener un `Target` para que el transpilador no necesite ningún SWAP con ella?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Un backend es un Target más la forma de ejecutar. [[r2]]El Target describe instrucciones, conectividad, errores y tiempos. [[r3]]El mapa de acoplamiento decide cuántos SWAP harán falta.
             [[r4]]Y con add instruction puedes describir cualquier dispositivo, real o imaginario.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["represent-quantum-computers", "custom-backend"],
    practice=[
        "Amplía `MiBackend` a una cadena de 5 qubits y transpila un GHZ de 5: ¿cuántos SWAP hacen falta?",
        "Copia el `FakeLOCCBackend` de la guía original y dibújalo con `plot_gate_map` (necesita graphviz).",
    ],
)

# ------------------------------------------------------------------ 3.5 Pass managers y DD
s_cierre, a_cierre = resumen(
    [
        "`PassManager([pases])` y `.run(qc)`",
        "`StagedPassManager(stages=[…], init=…, translation=…)`",
        "sustituir etapas de un preset: `pm.pre_layout = …`",
        "DD: `ALAPScheduleAnalysis` + `PadDynamicalDecoupling` (+ `BasisTranslator`)",
    ]
)
pass_managers = lesson(
    "p3-pass-managers",
    "Pass managers y desacoplamiento dinámico",
    "Crear pass managers propios, pass managers por etapas, modificar uno prediseñado y construir un pass manager de desacoplamiento dinámico.",
    [
        "crear un `PassManager` con pases de `qiskit.transpiler.passes`",
        "construir y modificar un `StagedPassManager`",
        "añadir desacoplamiento dinámico a un circuito transpilado",
    ],
    [
        beat(
            "propio",
            ("", "Un pass manager propio"),
            """El módulo qiskit punto transpiler punto passes tiene muchísimos pases para armar tu propio pass manager. Basta con pasarle una lista.
             [[ej]]Este junta las puertas de dos qubits que van seguidas en bloques, [[cons]]los consolida en una sola unitaria, [[syn]]y la sintetiza en las puertas RX, RY y RXX, las de un computador de iones atrapados, por ejemplo.
             [[res]]Aplicado a una Hadamard seguida de dos CX, el resultado solo contiene esas tres puertas.""",
            [
                Code(
                    """from qiskit import QuantumCircuit
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import Collect2qBlocks, ConsolidateBlocks, UnitarySynthesis

basis_gates = ["rx", "ry", "rxx"]
translate = PassManager([
    Collect2qBlocks(),
    ConsolidateBlocks(basis_gates=basis_gates),
    UnitarySynthesis(basis_gates),
])
circuit = QuantumCircuit(2)
circuit.h(0)
circuit.cx(0, 1)
circuit.cx(1, 0)
print(sorted(translate.run(circuit).count_ops()))""",
                    id="c",
                    size=22,
                ),
                Out("['rx', 'rxx', 'ry']", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="ej", lines=[7]),
                A("hl", "c", at="cons", lines=[8]),
                A("hl", "c", at="syn", lines=[9]),
                A("show", "o", at="res"),
            ],
        ),
        beat(
            "staged",
            ("", "Un pass manager por etapas"),
            """Un StagedPassManager está un nivel más arriba: en vez de pases, contiene pass managers, uno por etapa.
             [[ej]]Aquí declaramos dos etapas, init y translation. [[init]]init sintetiza unitarias de tres o más qubits y desarma las puertas grandes; [[trans]]translation es el pass manager que acabamos de crear.
             [[lim]]No hay límite al número de etapas.""",
            [
                Code(
                    """from qiskit.transpiler import StagedPassManager
from qiskit.transpiler.passes import Unroll3qOrMore

init = PassManager([UnitarySynthesis(basis_gates, min_qubits=3), Unroll3qOrMore()])
staged_pm = StagedPassManager(
    stages=["init", "translation"], init=init, translation=translate)""",
                    id="c",
                ),
                Flow(
                    [
                        dict(t="init", s="síntesis ≥3 qubits · Unroll3qOrMore"),
                        dict(t="translation", s="bloques → rx, ry, rxx"),
                    ],
                    id="f",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="ej", range="5-6"),
                A("show", "f", at="ej"),
                A("hl", "c", at="init", lines=[4]),
                A("step", "f", at="init", i=0),
                A("step", "f", at="trans", i=1),
            ],
        ),
        beat(
            "huecos",
            ("", "Antes de ejecutar"),
            """Otra forma muy útil: partir de uno prediseñado y cambiar algunas etapas. [[sub]]Cada una de las seis etapas tiene además una etapa previa, pre, y otra posterior, post, vacías por defecto. Apuesta: ¿cuántas etapas verá el pass manager en total?""",
            [
                Flow(
                    [
                        dict(t="pre_layout", s="vacía por defecto"),
                        dict(t="layout", s="la etapa", color="teal"),
                        dict(t="post_layout", s="vacía por defecto"),
                    ],
                    id="f",
                )
            ],
            ask=predict(
                "Para un pass manager prediseñado, ¿cuánto vale `len(pm.expanded_stages)`?",
                ["6", "12", "18", "24"],
                "Anotado. Lo comprobamos en el código.",
            ),
        ),
        beat(
            "modificar",
            ("", "Modificar un pass manager prediseñado"),
            """Ahora el código. [[sub]]Seis etapas, cada una con su pre y su post: seis por tres, dieciocho. Si apostaste por dieciocho, acertaste.
             [[ej]]Aquí añadimos una etapa pre layout con InverseCancellation, que elimina pares de puertas inversas, como T seguida de T daga, antes de elegir el layout.
             [[gen]]Las funciones generadoras de etapas, como generate embed passmanager, ayudan a construir etapas comunes.""",
            [
                Code(
                    """import numpy as np
from qiskit.circuit.library import HGate, RXGate, PhaseGate, TGate, TdgGate
from qiskit.transpiler import generate_preset_pass_manager
from qiskit.transpiler.passes import InverseCancellation
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

pass_manager = generate_preset_pass_manager(3, FakeSherbrooke())
pass_manager.pre_layout = PassManager([InverseCancellation([
    HGate(),
    (RXGate(np.pi / 4), RXGate(-np.pi / 4)),
    (PhaseGate(np.pi / 4), PhaseGate(-np.pi / 4)),
    (TGate(), TdgGate()),
])])
print(len(pass_manager.expanded_stages))""",
                    id="c",
                    size=21,
                ),
                Out("18", id="o", hidden=True, check=True),
            ],
            [A("show", "o", at="sub"), A("hl", "c", at="ej", range="8-13")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Una pregunta sobre etapas.""",
            [
                T(
                    "Quieres un pase que se ejecute justo después de calcular los tiempos de cada puerta.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué atributo asignas?",
                ["`pre_scheduling`", "`post_scheduling`", "`post_init`", "`pre_init`"],
                1,
                "Correcto: `post_scheduling` corre tras la etapa de scheduling, cuando ya existen las esperas.",
                wrong=[
                    "`pre_scheduling` va antes de calcular los tiempos.",
                    None,
                    "`post_init` va justo después de la etapa init, mucho antes.",
                    "`pre_init` es lo primero de todo.",
                ],
            ),
        ),
        beat(
            "dd",
            ("", "Desacoplamiento dinámico"),
            """Ahora un ejemplo avanzado: un pass manager que aplica desacoplamiento dinámico, una técnica de supresión de errores.
             [[idea]]Mientras un qubit espera ocioso, el entorno lo va desfasando. Si le aplicamos una secuencia de pulsos que en total es la identidad, por ejemplo X, Y, X, Y, lo volteamos sobre la esfera de Bloch y el efecto del ruido se cancela, como los pulsos de reenfoque en resonancia magnética nuclear.
             [[cuando]]Funciona mejor cuando hay mucho tiempo ocioso: qubits esperando mientras otros trabajan.""",
            [
                Flow(
                    [
                        dict(t="espera"),
                        dict(t="X", color="blue"),
                        dict(t="espera"),
                        dict(t="Y", color="violet"),
                        dict(t="espera"),
                        dict(t="X", color="blue"),
                        dict(t="espera"),
                        dict(t="Y", color="violet"),
                        dict(t="espera"),
                    ],
                    id="f",
                ),
                M(r"XYXY=\mathbb 1\ \ (\text{salvo fase})", id="m", hidden=True, size=40),
            ],
            [A("show", "m", at="idea"), A("step", "f", at="cuando", i=[0, 2, 4, 6, 8])],
        ),
        beat(
            "ddcode",
            ("", "El pass manager de DD"),
            """Paso a paso. [[tr]]Primero transpilamos el circuito al backend: el desacoplamiento se añade después de transpilar y programar los tiempos.
             [[y]]La puerta Y no es base de Sherbrooke, así que hay que añadirla al Target con la duración y el error de la X, que son iguales.
             [[pm]]Luego, un PassManager con dos pases: ALAPScheduleAnalysis, que calcula cuándo empieza cada instrucción, y PadDynamicalDecoupling, que llena las esperas con la secuencia.
             [[bt]]Por último, BasisTranslator convierte las Y en puertas base. El circuito queda listo, con instrucciones Delay explícitas.""",
            [
                Code(
                    """from qiskit.circuit.library import XGate, YGate, efficient_su2
from qiskit.transpiler import InstructionProperties
from qiskit.transpiler.passes import BasisTranslator
from qiskit.transpiler.passes.scheduling import ALAPScheduleAnalysis, PadDynamicalDecoupling
from qiskit.circuit.equivalence_library import SessionEquivalenceLibrary as sel

target = FakeSherbrooke().target
basis_gates = list(target.operation_names)
qc = efficient_su2(12, entanglement="circular", reps=1)
qc_t = generate_preset_pass_manager(1, target=target, seed_transpiler=12345).run(qc)
qc_t.assign_parameters(np.random.default_rng(1234).uniform(-np.pi, np.pi, qc_t.num_parameters), inplace=True)

target.add_instruction(YGate(), {(q,): InstructionProperties(
    duration=target["x"][(q,)].duration, error=target["x"][(q,)].error) for q in range(target.num_qubits)})

dd_pm = PassManager([ALAPScheduleAnalysis(target=target),
                     PadDynamicalDecoupling(target=target, dd_sequence=[XGate(), YGate(), XGate(), YGate()])])
qc_dd = BasisTranslator(sel, basis_gates)(dd_pm.run(qc_t))
print("delay" in qc_dd.count_ops(), "y" in qc_dd.count_ops())""",
                    id="c",
                    size=17,
                ),
                Out("True False", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="tr", range="8-10"),
                A("hl", "c", at="y", range="12-13"),
                A("hl", "c", at="pm", range="15-16"),
                A("hl", "c", at="bt", range="17-18"),
                A("show", "o", at="bt", t=2),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Sobre el orden de los pases.""",
            [
                T(
                    "Aplicas `PadDynamicalDecoupling` a un circuito abstracto, antes de transpilar.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué problema hay?",
                [
                    "ninguno",
                    "aún no se sabe cuánto esperará cada qubit: falta transpilar y programar tiempos",
                    "el DD solo funciona en simuladores",
                ],
                1,
                "Correcto: las esperas dependen del layout, del routing y de la duración real de cada puerta; por eso el DD va al final.",
                wrong=[
                    "Sin tiempos no hay esperas que llenar.",
                    None,
                    "El DD se usa precisamente en hardware real.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Primero, arma un pass manager que traduce a las puertas de un computador de iones atrapados. [[n2]]Después, cambia el pase de cancelación que vive en la etapa pre layout de uno prediseñado.
             [[n3]]Y por último, construye tú el pass manager de desacoplamiento dinámico sobre un circuito ya programado, y comprueba que no cambia el operador.""",
            [
                Exercise(
                    "p3-pass-managers/traducir-iones",
                    "Completa `traducir`, un pass manager que traduce un circuito a las puertas de un computador de iones atrapados: `rx`, `ry` y `rxx`. Ya reúne las puertas de dos qubits en bloques y consolida cada bloque en una unitaria; falta el pase que escribe esa unitaria con `puertas_iones`.",
                    level=1,
                    id="e1",
                    hidden=True,
                    hints=[
                        "Consolidar deja una puerta `unitary`, que todavía no es ninguna puerta base.",
                        "Hay un pase de síntesis que convierte una unitaria en puertas de un conjunto dado.",
                        "El pase se llama `UnitarySynthesis` y va al final de la lista, después de consolidar.",
                    ],
                ),
                Exercise(
                    "p3-pass-managers/cancelar-pares",
                    "`pm_nivel0.pre_layout` cancela pares T y T†, pero este circuito tiene otros: una `S` seguida de `S†` y dos `H` seguidas. Cambia el pase para que, con el nivel 0, el circuito dé lo mismo que el que no los tiene.",
                    level=2,
                    id="e2",
                    hidden=True,
                    hints=[
                        "`InverseCancellation` solo cancela los pares que le nombras.",
                        "La `H` es su propia inversa; `S` y `S†` se anulan entre sí.",
                        "Cada elemento de la lista es una puerta sola, si es su propia inversa, o una tupla con una puerta y su inversa.",
                    ],
                ),
                Exercise(
                    "p3-pass-managers/dd-pm",
                    "Rellena `dd_pm` con **dos pases**, en este orden: `ALAPScheduleAnalysis` y `PadDynamicalDecoupling`. Los dos reciben `target=objetivo`, y el segundo, además, `dd_sequence` con la secuencia X, X. "
                    "El circuito `programado` ya tiene tiempos asignados. Trampa: el análisis de tiempos va antes del relleno; al revés, el relleno no sabe cuánto dura cada espera.",
                    level=3,
                    id="e3",
                    hidden=True,
                    hints=[
                        "El relleno de DD necesita saber cuánto dura cada espera, y ese dato lo produce un análisis previo.",
                        "Los dos pases viven en `qiskit.transpiler.passes.scheduling` y se ejecutan en el orden en que los pones en la lista.",
                        "El análisis recibe `target=`; el relleno recibe `target=` y `dd_sequence=`, una lista con dos puertas `X`.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma, conectadas con tu proyecto.""",
            [T("Cada etapa es un punto donde puedes meter tu propio pase.", "subtitle")],
            ask=reflect(
                "`PadDynamicalDecoupling` necesita las duraciones de las puertas. ¿Qué información del `Target` le haría falta a un chip inventado para poder usarlo?",
                "En tu cadena Ising, los qubits de los extremos esperan mientras los del centro trabajan. ¿En qué etapa del pass manager pondrías un pase para aprovechar eso, y por qué ahí?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Un PassManager es una lista de pases. [[r2]]Un StagedPassManager organiza pass managers por etapas. [[r3]]Puedes sustituir cualquier etapa de uno prediseñado, incluidas las pre y post.
             [[r4]]Y el desacoplamiento dinámico se añade al final, con análisis de tiempos y relleno.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["transpile-with-pass-managers", "dynamical-decoupling-pass-manager"],
    practice=[
        "Dibuja `qc_dd` con `timeline_drawer(qc_dd, idle_wires=False, target=target)` y busca las secuencias XYXY.",
        "Prueba la secuencia `[XGate(), XGate()]` y compara cuántas puertas añade frente a XY4.",
    ],
)

# ------------------------------------------------------------------ 3.6 Pases propios y DAG
s_cierre, a_cierre = resumen(
    [
        "el transpilador trabaja sobre un DAG: nodos de entrada, operación y salida",
        "`AnalysisPass` (lee, escribe `property_set`) · `TransformationPass` (modifica el DAG)",
        "`op_nodes`, `apply_operation_back/front`, `substitute_node_with_dag`, `dag_to_circuit`",
        "ejemplos: `PauliTwirl` y `BasicSwap`",
    ]
)
pases = lesson(
    "p3-pases-propios",
    "Escribir pases propios: el DAG",
    "La representación DAG de un circuito, sus operaciones básicas y dos pases escritos desde cero: twirling de Pauli y un mapeador básico con SWAP.",
    [
        "describir la representación DAG de un circuito",
        "distinguir pases de análisis y de transformación",
        "escribir un `TransformationPass` que modifique el DAG",
    ],
    [
        beat(
            "dag",
            ("", "Circuitos como grafos"),
            """Dentro del transpilador, los circuitos no son listas de puertas: son grafos dirigidos acíclicos, DAG.
             [[nodos]]Hay tres clases de nodos: de entrada, uno por qubit y bit clásico; de operación, uno por instrucción; y de salida. [[aristas]]Cada arista indica un flujo de datos, una dependencia: esta operación necesita el resultado de aquella.
             [[ventaja]]La ventaja frente a una lista es que el DAG muestra directamente qué operaciones dependen de cuáles, y cuáles se pueden reordenar o ejecutar en paralelo.""",
            [
                Flow(
                    [
                        dict(t="q₀ entrada", color="green"),
                        dict(t="H", color="blue"),
                        dict(t="CX", color="blue"),
                        dict(t="medir", color="blue"),
                        dict(t="if → RZ", color="blue"),
                        dict(t="salida", color="red"),
                    ],
                    id="f",
                    stagger=True,
                ),
                T(
                    "verde: entradas · azul: operaciones · rojo: salidas",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("item", "f", at="dag", i=0),
                A("item", "f", at="nodos", i=1),
                A("item", "f", at="nodos", t=0.5, i=2),
                A("item", "f", at="nodos", t=1, i=3),
                A("item", "f", at="nodos", t=1.5, i=4),
                A("item", "f", at="nodos", t=2, i=5),
                A("show", "n", at="aristas"),
            ],
        ),
        beat(
            "ops",
            ("", "Operaciones con el DAG"),
            """circuit to dag convierte un circuito en DAG. [[nodes]]op nodes devuelve los nodos de operación; cada uno tiene su operación, sus qubits y sus bits.
             [[back]]apply operation back añade una operación al final; [[front]]apply operation front, al principio.
             [[sub]]substitute node with dag reemplaza un nodo por un DAG pequeño, conservando las conexiones. [[vuelta]]Y dag to circuit convierte de vuelta. Así trabaja todo el transpilador: circuito a DAG, transformaciones, DAG a circuito.""",
            [
                Code(
                    """from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.circuit.library import HGate, CCXGate

q = QuantumRegister(3, "q")
c = ClassicalRegister(3, "c")
circ = QuantumCircuit(q, c)
circ.h(q[0])
circ.cx(q[0], q[1])
circ.measure(q[0], c[0])
with circ.if_test((c, 2)):
    circ.rz(0.5, q[1])

dag = circuit_to_dag(circ)
print([node.name for node in dag.op_nodes()])
dag.apply_operation_back(HGate(), qargs=[q[0]])
dag.apply_operation_front(CCXGate(), qargs=[q[0], q[1], q[2]])
print(dag_to_circuit(dag).count_ops())""",
                    id="c",
                    size=20,
                ),
                Out(
                    """['h', 'cx', 'measure', 'if_else']
OrderedDict({'h': 2, 'ccx': 1, 'cx': 1, 'measure': 1, 'if_else': 1})""",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="ops", lines=[14]),
                A("hl", "c", at="nodes", lines=[15]),
                A("hl", "c", at="back", lines=[16]),
                A("hl", "c", at="front", lines=[17]),
                A("hl", "c", at="vuelta", lines=[18]),
                A("show", "o", at="vuelta"),
            ],
        ),
        beat(
            "tipos",
            ("", "Dos tipos de pases"),
            """Los pases son de dos tipos. [[an]]Los de análisis, AnalysisPass, leen el DAG y escriben lo que averiguan en el property set, un diccionario compartido; no pueden modificar el DAG.
             [[tr]]Los de transformación, TransformationPass, modifican el DAG y pueden leer el property set, pero no escribir en él.
             [[run]]En ambos casos, lo que implementas es el método run, que recibe el DAG.""",
            [
                Row(
                    Box(
                        "def",
                        "AnalysisPass",
                        L(
                            ["lee el DAG", "**escribe** en `property_set`", "no modifica el DAG"],
                            size=26,
                        ),
                        id="a",
                        hidden=True,
                    ),
                    Box(
                        "idea",
                        "TransformationPass",
                        L(
                            ["**modifica** el DAG", "lee `property_set`", "devuelve el DAG nuevo"],
                            size=26,
                        ),
                        id="b",
                        hidden=True,
                    ),
                    gap=26,
                ),
                Code("def run(self, dag): ...", id="c", hidden=True),
            ],
            [A("show", "a", at="an"), A("show", "b", at="tr"), A("show", "c", at="run")],
        ),
        beat(
            "twirl",
            ("", "Un pase de twirling de Pauli"),
            """Primer pase propio: twirling de Pauli, una técnica que aleatoriza cómo los qubits sufren el ruido de las puertas de dos qubits, las más ruidosas.
             [[pares]]Rodeamos cada puerta con dos Paulis elegidos para que el efecto total sea el mismo: Pauli a la izquierda, puerta, Pauli a la derecha. Los pares válidos se encuentran probando todas las combinaciones de Paulis de dos qubits.
             [[run]]En run recorremos los nodos, [[mini]]construimos un DAG pequeño con el Pauli, la puerta y el otro Pauli, [[subst]]y sustituimos el nodo original por ese mini DAG.""",
            [
                Code(
                    """import numpy as np
from qiskit.dagcircuit import DAGCircuit
from qiskit.circuit.library import CXGate, ECRGate
from qiskit.transpiler import PassManager
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.quantum_info import Operator, pauli_basis

class PauliTwirl(TransformationPass):
    def __init__(self, gates_to_twirl=None):
        super().__init__()
        self.gates_to_twirl = gates_to_twirl or [CXGate(), ECRGate()]
        self.twirl_set = {}
        for gate in self.gates_to_twirl:
            self.twirl_set[gate.name] = [
                (left, right) for left in pauli_basis(2) for right in pauli_basis(2)
                if (Operator(left) @ Operator(gate)).equiv(Operator(gate) @ right)]

    def run(self, dag):
        classes = tuple(g.base_class for g in self.gates_to_twirl)
        for node in dag.op_nodes():
            if not isinstance(node.op, classes):
                continue
            left, right = self.twirl_set[node.op.name][np.random.randint(16)]
            mini_dag = DAGCircuit()
            reg = QuantumRegister(2)
            mini_dag.add_qreg(reg)
            mini_dag.apply_operation_back(left.to_instruction(), [reg[0], reg[1]])
            mini_dag.apply_operation_back(node.op, [reg[0], reg[1]])
            mini_dag.apply_operation_back(right.to_instruction(), [reg[0], reg[1]])
            dag.substitute_node_with_dag(node, mini_dag)
        return dag""",
                    id="c",
                    size=16,
                )
            ],
            [
                A("hl", "c", at="pares", range="13-16"),
                A("hl", "c", at="run", range="18-22"),
                A("hl", "c", at="mini", range="23-29"),
                A("hl", "c", at="subst", range="30-31"),
            ],
        ),
        beat(
            "twirl2",
            ("", "Probar el pase"),
            """Probemos el pase sobre un circuito con CX y ECR. [[pm]]Lo ponemos en un PassManager y generamos cincuenta circuitos, cada uno con Paulis aleatorios distintos.
             [[igual]]Cada puerta de dos qubits queda entre dos Paulis. Y la comprobación clave: todos los circuitos implementan exactamente el mismo operador que el original.""",
            [
                Code(
                    """qc = QuantumCircuit(3)
qc.cx(0, 1)
qc.ecr(1, 2)
qc.ecr(1, 0)
qc.cx(2, 1)
pm = PassManager([PauliTwirl()])
twirled = [pm.run(qc) for _ in range(50)]
print(all(Operator(t).equiv(qc) for t in twirled))""",
                    id="c",
                ),
                Out("True", id="o", hidden=True, check=True),
                Circ(
                    2,
                    [G("box", 0, 1, label="P"), G("cx", 0, 1), G("box", 0, 1, label="P′")],
                    id="q",
                ),
            ],
            [
                A("hl", "c", at="pm", range="6-7"),
                A("show", "o", at="igual"),
                A("hl", "c", at="igual", lines=[8]),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Sobre los pares de twirling.""",
            [M(r"P_L\cdot \mathrm{CX} = \mathrm{CX}\cdot P_R", size=46)],
            ask=numeric(
                "Hay 16 Paulis de dos qubits para $P_L$. ¿Cuántos pares $(P_L, P_R)$ válidos tiene la CX?",
                16,
                "Correcto: para cada $P_L$ hay exactamente un $P_R=\\mathrm{CX}^\\dagger P_L\\mathrm{CX}$, que es otro Pauli porque la CX es de Clifford. 16 pares.",
                tol=0.001,
                hint="La CX lleva Paulis a Paulis (es una puerta de Clifford).",
            ),
        ),
        beat(
            "apuesta",
            ("", "Antes de ejecutar"),
            """Segundo ejemplo: un pase de routing muy simple, BasicSwap. Si los qubits de una puerta no son vecinos, inserta SWAP a lo largo del camino más corto, y el layout se actualiza con cada uno.
             [[reto]]Tenemos una línea de siete qubits, y un circuito con una CX entre los qubits cero y cuatro, y otra entre el seis y el uno. Apuesta: ¿cuántos SWAP inserta en total?""",
            [
                Graph(
                    nodes=[[k, 0] for k in range(7)],
                    edges=[[k, k + 1] for k in range(6)],
                    unit=56,
                    r=18,
                    id="g",
                ),
                Circ(7, [G("h", 0), G("cx", 0, 4), G("cx", 6, 1)], id="q", scale=0.55),
            ],
            ask=predict(
                "¿Cuántos `swap` inserta `BasicSwap` en la línea de 7 qubits?",
                ["3", "5", "8", "12"],
                "Anotado. Veamos el pase y su resultado.",
            ),
        ),
        beat(
            "basicswap",
            ("", "Un mapeador básico"),
            """Aquí está el pase. [[capas]]Recorre el DAG capa por capa; en cada capa, las operaciones actúan sobre qubits distintos.
             [[chk]]Para cada puerta de dos qubits mira si sus qubits físicos están a distancia uno en el mapa de acoplamiento. [[swap]]Si no, busca el camino más corto e inserta SWAP a lo largo de él, actualizando el layout.
             [[prueba]]Y el resultado: ocho SWAP. La primera CX necesita tres, porque entre el cero y el cuatro hay cuatro saltos; la segunda necesita cinco, porque el primer grupo de SWAP ya movió los estados. Si apostaste por ocho, acertaste.""",
            [
                Code(
                    """from qiskit.transpiler import Layout, CouplingMap
from qiskit.circuit.library import SwapGate

class BasicSwap(TransformationPass):
    def __init__(self, coupling_map):
        super().__init__()
        self.coupling_map = coupling_map

    def run(self, dag):
        new_dag = dag.copy_empty_like()
        layout = Layout.generate_trivial_layout(*dag.qregs.values())
        for layer in dag.serial_layers():
            subdag = layer["graph"]
            for gate in subdag.two_qubit_ops():
                p0, p1 = layout[gate.qargs[0]], layout[gate.qargs[1]]
                if self.coupling_map.distance(p0, p1) != 1:
                    path = self.coupling_map.shortest_undirected_path(p0, p1)
                    for i in range(len(path) - 2):
                        new_dag.apply_operation_back(SwapGate(), [layout[path[i]], layout[path[i + 1]]])
                        layout.swap(path[i], path[i + 1])
            new_dag.compose(subdag, qubits=layout.reorder_bits(new_dag.qubits))
        return new_dag

circ = QuantumCircuit(7)
circ.h(0)
circ.cx(0, 4)
circ.cx(6, 1)
out = PassManager([BasicSwap(CouplingMap.from_line(7))]).run(circ)
print(out.count_ops()["swap"])""",
                    id="c",
                    size=16,
                ),
                Out("8", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="capas", range="11-12"),
                A("hl", "c", at="chk", range="13-15"),
                A("hl", "c", at="swap", range="16-19"),
                A("hl", "c", at="prueba", range="23-28"),
                A("show", "o", at="prueba"),
            ],
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Primero, escribe la función que convierte un circuito en DAG, añade puertas al principio y al final, y vuelve al circuito. [[n2]]Después, completa un pase de transformación que sustituye cada SWAP por tres CNOT.
             [[n3]]Y por último, escribe tú un pase de análisis que cuenta las puertas de dos qubits y las guarda en el property set.""",
            [
                Exercise(
                    "p3-pases-propios/dag-operaciones",
                    "Completa `envolver(circuito)`: convierte el circuito en DAG, añade una `H` al final sobre el qubit 0 y una Toffoli (`CCXGate`) al principio sobre los qubits 0, 1 y 2, y vuelve al circuito. "
                    "Trampa: los qubits que recibe el DAG son sus propios objetos (`dag.qubits`), no los de un registro que tú llames `q`.",
                    level=1,
                    id="e1",
                    hidden=True,
                    hints=[
                        "Un DAG permite añadir operaciones por los dos extremos sin recorrer el circuito.",
                        "Hay un método para añadir al final y otro para añadir al principio; los dos reciben la puerta y sus `qargs`.",
                        "Los qubits que pasas son objetos del DAG, como `dag.qubits[0]`, no números.",
                    ],
                ),
                Exercise(
                    "p3-pases-propios/swap-a-cx",
                    "Cambia `SwapACx` para que sustituya cada `swap` por tres `cx`: (0, 1), (1, 0) y (0, 1), sobre los dos qubits del mini DAG `reg`. La comprobación exige el mismo operador y ningún `swap`.",
                    level=2,
                    id="e2",
                    hidden=True,
                    hints=[
                        "Un SWAP intercambia dos qubits, y lo mismo se logra con tres CNOT que alternan quién es el control.",
                        "El cambio va dentro del mini DAG `mini`, en lugar de la línea que añade `SwapGate()`.",
                        "Añade cada `CXGate()` con `apply_operation_back`, con los dos qubits de `reg` en el orden (control, objetivo).",
                    ],
                ),
                Exercise(
                    "p3-pases-propios/contar-dos-qubits",
                    'Escribe `ContarDosQubits`, un `AnalysisPass` cuyo método `run(self, dag)` cuenta las puertas de exactamente dos qubits de `dag` y guarda el número en `self.property_set["n2q"]`, sin tocar el DAG. '
                    "Trampas: si no hay ninguna, guarda 0 (no dejes la clave sin escribir), y una Toffoli tiene tres qubits, así que no cuenta.",
                    level=3,
                    id="e3",
                    hidden=True,
                    hints=[
                        "Un pase de análisis lee el DAG y deja su resultado en el `property_set`; no lo modifica.",
                        "El DAG sabe filtrar sus operaciones por número de qubits.",
                        "`dag.two_qubit_ops()` devuelve las operaciones de dos qubits; el `property_set` se usa como un diccionario.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma, conectadas con tu proyecto.""",
            [T("Primero se mide, después se cambia.", "subtitle")],
            ask=reflect(
                "Qiskit separa los pases de análisis de los de transformación. ¿Qué problemas te evita esa separación al encadenar muchos pases?",
                "En tu cadena Ising, cada `rzz` cuesta dos `cz`. ¿Qué pase escribirías, de análisis o de transformación, para ahorrar alguna?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]El transpilador trabaja sobre un DAG. [[r2]]Los pases de análisis escriben en el property set; los de transformación cambian el DAG. [[r3]]Las operaciones básicas son op nodes, apply operation, substitute node with dag y dag to circuit.
             [[r4]]Con eso escribimos un pase de twirling y un mapeador con SWAP.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["custom-transpiler-pass", "DAG-representation"],
    practice=[
        "Dibuja el DAG del circuito de la lección con `dag_drawer(dag)` (requiere graphviz).",
        'Escribe un `AnalysisPass` que cuente las puertas de dos qubits y lo guarde en `self.property_set["n2q"]`.',
    ],
)

# ------------------------------------------------------------------ 3.7 Plugins e IA
s_cierre, a_cierre = resumen(
    [
        "tres tipos de plugin: etapa, síntesis unitaria, síntesis de alto nivel",
        "usar: `*_method`, `unitary_synthesis_method`, `hls_config=HLSConfig(...)`",
        "crear: subclase + entry point en `pyproject.toml`",
        "IA: `AIRouting`, `AI*Synthesis`, `Collect*`, `generate_ai_pass_manager`",
    ]
)
plugins = lesson(
    "p3-plugins",
    "Plugins y transpilación con IA",
    "Los tres tipos de plugins del transpilador, cómo listarlos, usarlos y crearlos, y los pases de routing y síntesis con inteligencia artificial.",
    [
        "listar y usar plugins de etapa, de síntesis unitaria y de alto nivel",
        "crear un plugin y publicarlo con un entry point",
        "usar los pases de IA de `qiskit-ibm-transpiler`",
    ],
    [
        beat(
            "tipos",
            ("", "Tres tipos de plugins"),
            """Qiskit permite que paquetes de terceros añadan funciones al transpilador mediante plugins. Hay tres tipos.
             [[etapa]]Un plugin de etapa ofrece un pass manager que sustituye a una de las seis etapas. [[unit]]Un plugin de síntesis unitaria recibe una matriz y devuelve un circuito.
             [[hl]]Y un plugin de síntesis de alto nivel sintetiza objetos abstractos, como funciones lineales u operadores de Clifford.
             [[eco]]Varios plugins de terceros forman parte del ecosistema de Qiskit; se instalan con pip, por ejemplo qiskit toqm para el routing.""",
            [
                Table(
                    ["Tipo", "Entrada → salida", "Se usa con"],
                    [
                        [
                            "Etapa",
                            "reemplaza una de las 6 etapas",
                            "`layout_method=`, `routing_method=`…",
                        ],
                        ["Síntesis unitaria", "matriz → circuito", "`unitary_synthesis_method=`"],
                        [
                            "Síntesis de alto nivel",
                            "Clifford, función lineal… → circuito",
                            "`hls_config=`",
                        ],
                    ],
                    id="t",
                    stagger=True,
                    size=23,
                ),
                Sh("$ pip install qiskit-toqm", id="s", hidden=True),
            ],
            [
                A("item", "t", at="etapa", i=0),
                A("item", "t", at="unit", i=1),
                A("item", "t", at="hl", i=2),
                A("show", "s", at="eco"),
            ],
        ),
        beat(
            "listar",
            ("", "Ver qué plugins hay"),
            """Para cada tipo hay una función que lista lo instalado. [[stage]]list stage plugins, con el nombre de la etapa. [[unit]]unitary synthesis plugin names: aquí aparecen aqc, clifford, gridsynth y sk, el algoritmo de Solovay Kitaev.
             [[hl]]Y high level synthesis plugin names, con el tipo de objeto: para Clifford, seis nombres, contando default.""",
            [
                Code(
                    """from qiskit.transpiler.passes.synthesis import (
    unitary_synthesis_plugin_names, high_level_synthesis_plugin_names)

print(unitary_synthesis_plugin_names())
print(high_level_synthesis_plugin_names("clifford"))""",
                    id="c",
                ),
                Out(
                    """['aqc', 'clifford', 'default', 'gridsynth', 'sk']
['ag', 'bm', 'default', 'greedy', 'layers', 'lnn']""",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [A("show", "o", at="unit"), A("hl", "c", at="hl", lines=[5])],
        ),
        beat(
            "usar",
            ("", "Usar un plugin"),
            """Para usar un plugin de etapa, pasa su nombre en el argumento de esa etapa terminado en method: aquí, routing method igual a lookahead.
             [[unit]]Para síntesis unitaria, unitary synthesis method, y sus opciones en un diccionario libre, unitary synthesis plugin config.
             [[hls]]Para alto nivel, crea un HLSConfig con una lista de métodos por tipo de objeto: se prueban en orden hasta que uno funciona. Y pásalo como hls config.""",
            [
                Code(
                    """from qiskit.transpiler import generate_preset_pass_manager
from qiskit.transpiler.passes import HLSConfig
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

backend = FakeSherbrooke()
pm1 = generate_preset_pass_manager(3, backend=backend, routing_method="lookahead")
pm2 = generate_preset_pass_manager(3, backend=backend,
    unitary_synthesis_method="sk",
    unitary_synthesis_plugin_config=dict(basis_gates=["cz", "id", "rz", "sx", "x"]))
hls_config = HLSConfig(clifford=["layers"], linear_function=["pmh"])
pm3 = generate_preset_pass_manager(3, backend=backend, hls_config=hls_config)""",
                    id="c",
                    size=22,
                )
            ],
            [
                A("hl", "c", at="usar", lines=[6]),
                A("hl", "c", at="unit", range="7-9"),
                A("hl", "c", at="hls", range="10-11"),
            ],
        ),
        beat(
            "crear",
            ("", "Crear un plugin"),
            """Crear un plugin es una gran forma de compartir tu trabajo. Son dos pasos. [[sub]]Primero, una subclase de la clase abstracta adecuada: PassManagerStagePlugin, UnitarySynthesisPlugin o HighLevelSynthesisPlugin.
             [[ej]]Este plugin de layout implementa pass manager: ejecuta VF2Layout con más intentos cuanto mayor el nivel de optimización, y luego incrusta el layout en el dispositivo.
             [[ep]]Segundo, exponerlo como entry point en los metadatos del paquete, por ejemplo en pyproject punto toml. [[nombres]]Cada plugin necesita un nombre único; los nombres que usa Qiskit, como default o sk, están reservados.""",
            [
                Code(
                    """from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import VF2Layout
from qiskit.transpiler.preset_passmanagers import common
from qiskit.transpiler.preset_passmanagers.plugin import PassManagerStagePlugin

class MyLayoutPlugin(PassManagerStagePlugin):
    def pass_manager(self, pass_manager_config, optimization_level=None):
        layout_pm = PassManager([VF2Layout(
            coupling_map=pass_manager_config.coupling_map,
            max_trials=optimization_level * 10 + 1,
            target=pass_manager_config.target)])
        layout_pm += common.generate_embed_passmanager(pass_manager_config.coupling_map)
        return layout_pm""",
                    id="c",
                    size=21,
                ),
                Code(
                    '''[project.entry-points."qiskit.transpiler.layout"]
"my_layout" = "my_qiskit_plugin:MyLayoutPlugin"''',
                    "text",
                    title="pyproject.toml",
                    id="t",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="sub", lines=[6]),
                A("hl", "c", at="ej", range="7-13"),
                A("show", "t", at="ep"),
            ],
        ),
        beat(
            "otros",
            ("", "Plugins de síntesis"),
            """Los otros dos tipos siguen el mismo esquema. [[unit]]Un UnitarySynthesisPlugin implementa run, que recibe una matriz de NumPy y devuelve un DAGCircuit, y declara qué admite con propiedades como supports basis gates o supports coupling map.
             [[hl]]Un HighLevelSynthesisPlugin implementa run, que recibe el objeto, por ejemplo un Clifford, y devuelve un QuantumCircuit; o None si no puede sintetizarlo, y entonces se prueba el siguiente método.
             [[ep]]Los entry points son qiskit punto unitary synthesis y qiskit punto synthesis; en este último, el nombre lleva el tipo de objeto, punto, el nombre del plugin.""",
            [
                Code(
                    """from qiskit.synthesis import synth_clifford_bm
from qiskit.transpiler.passes.synthesis.plugin import HighLevelSynthesisPlugin

class MyCliffordSynthesisPlugin(HighLevelSynthesisPlugin):
    def run(self, high_level_object, coupling_map=None, target=None, qubits=None, **options):
        if high_level_object.num_qubits <= 3:
            return synth_clifford_bm(high_level_object)
        return None""",
                    id="c",
                    size=21,
                ),
                Code(
                    '''[project.entry-points."qiskit.synthesis"]
"clifford.my_clifford_synthesis" = "my_qiskit_plugin:MyCliffordSynthesisPlugin"''',
                    "text",
                    title="pyproject.toml",
                    id="t",
                    hidden=True,
                ),
            ],
            [A("hl", "c", at="hl", range="4-8"), A("show", "t", at="ep")],
        ),
        beat(
            "apuesta",
            ("", "Antes de ejecutar"),
            """Pongamos a prueba ese plugin. [[lista]]Lo pasamos a un HLSConfig seguido de greedy, un método que ya trae Qiskit: se prueban en orden, y el primero que devuelve un circuito gana.
             [[reto]]Y le damos un Clifford de cinco qubits. Apuesta: ¿quién lo sintetiza?""",
            [
                Flow(
                    [
                        dict(t="MyCliffordSynthesisPlugin", s="solo hasta 3 qubits", color="blue"),
                        dict(t="greedy", s="método de Qiskit", color="teal"),
                    ],
                    id="f",
                    stagger=True,
                ),
                T("Clifford aleatorio de 5 qubits", "note"),
            ],
            [A("item", "f", at="lista", i=0), A("item", "f", at="lista", t=1, i=1)],
            ask=predict(
                'Con `clifford=[MyCliffordSynthesisPlugin(), "greedy"]` y un Clifford de 5 qubits, ¿quién lo sintetiza?',
                ["mi plugin", "`greedy`", "nadie: queda un `clifford` sin sintetizar", "da error"],
                "Anotado. Lo comprobamos con y sin el método de respaldo.",
            ),
        ),
        beat(
            "respaldo",
            ("", "Un método de respaldo"),
            """Probamos con dos Clifford, de tres y de cinco qubits, y dos configuraciones. [[solo]]Con mi plugin solo, el de tres qubits se sintetiza, pero el de cinco queda como un Clifford sin tocar: mi plugin devolvió None. [[resp]]Con greedy detrás, se sintetizan los dos.
             [[res]]Si apostaste por greedy, acertaste: devolver None no es un error, es la señal de pasar al siguiente método.""",
            [
                Code(
                    """from qiskit import QuantumCircuit
from qiskit.quantum_info import random_clifford
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import HLSConfig, HighLevelSynthesis

def sin_sintetizar(n, metodos):
    qc = QuantumCircuit(n)
    qc.append(random_clifford(n, seed=1), range(n))
    out = PassManager([HighLevelSynthesis(hls_config=HLSConfig(clifford=metodos))]).run(qc)
    return "clifford" in out.count_ops()

solo = [(MyCliffordSynthesisPlugin(), {})]
con_respaldo = [(MyCliffordSynthesisPlugin(), {}), "greedy"]
for n in (3, 5):
    print(n, sin_sintetizar(n, solo), sin_sintetizar(n, con_respaldo))""",
                    id="c",
                    size=19,
                ),
                Out("3 False False\n5 True False", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="solo", lines=[14]),
                A("hl", "c", at="resp", lines=[15]),
                A("show", "o", at="solo"),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Una pregunta sobre plugins.""",
            [
                T(
                    "Tu algoritmo recibe un operador de Clifford y devuelve un circuito corto.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué tipo de plugin escribes?",
                ["de etapa", "de síntesis unitaria", "de síntesis de alto nivel"],
                2,
                "Correcto: los Clifford son objetos de alto nivel; tu plugin se registra como `clifford.<nombre>` en `qiskit.synthesis`.",
                wrong=[
                    "Un plugin de etapa reemplaza una etapa entera del transpilador.",
                    "La síntesis unitaria recibe una matriz, no un objeto Clifford.",
                    None,
                ],
            ),
        ),
        beat(
            "ia",
            ("", "Pases con inteligencia artificial"),
            """Por último, los pases de transpilación con inteligencia artificial, en beta. Sustituyen a pases tradicionales y suelen dar mejores resultados, con menos profundidad y menos CNOT, siendo mucho más rápidos que métodos exactos como los resolvedores de satisfacibilidad. Se ejecutan en tu computadora.
             [[inst]]Vienen en el paquete qiskit ibm transpiler. [[rout]]AIRouting hace layout y routing a la vez. Su layout mode puede ser keep, que respeta el layout anterior; improve, que lo usa como punto de partida; u optimize, el valor por defecto, que lo ignora.
             [[syn]]Y hay pases de síntesis: de Clifford y de funciones lineales hasta nueve qubits, de permutaciones de veintisiete, treinta y tres o sesenta y cinco qubits, y de redes de Pauli hasta seis.""",
            [
                Sh("$ pip install qiskit-ibm-transpiler", id="s"),
                Table(
                    ["Pase", "Qué hace"],
                    [
                        [
                            "`AIRouting`",
                            "layout + routing · `layout_mode`: `keep`, `improve`, `optimize`",
                        ],
                        ["`AICliffordSynthesis`", "bloques H, S, CX · hasta 9 qubits"],
                        ["`AILinearFunctionSynthesis`", "bloques CX y SWAP · hasta 9 qubits"],
                        ["`AIPermutationSynthesis`", "bloques SWAP · 27, 33 o 65 qubits"],
                        ["`AIPauliNetworkSynthesis`", "H, S, SX, CX, rotaciones · hasta 6 qubits"],
                    ],
                    id="t",
                    stagger=True,
                    size=22,
                ),
            ],
            [
                A("item", "t", at="rout", i=0),
                A("item", "t", at="syn", i=1),
                A("item", "t", at="syn", t=1, i=2),
                A("item", "t", at="syn", t=2, i=3),
                A("item", "t", at="syn", t=3, i=4),
            ],
        ),
        beat(
            "ia2",
            ("", "Usar los pases de IA"),
            """La forma típica: primero AIRouting, [[col]]luego un pase de recolección, que junta bloques del tipo adecuado y de tamaño admitido, [[syn]]y después el de síntesis, que los re-sintetiza. Por defecto solo reemplaza un bloque si el nuevo tiene menos CNOT.
             [[sub]]La síntesis necesita que el bloque esté sobre un subgrafo conexo del mapa de acoplamiento; si no, avisa y lo deja igual.
             [[hib]]También existe generate ai pass manager, que combina los pases heurísticos de Qiskit con los de IA, con un nivel para cada parte.
             [[hilos]]Y los pases usan varios hilos: se ajusta con max threads o la variable AI TRANSPILER MAX THREADS.""",
            [
                Code(
                    """from qiskit_ibm_transpiler.ai.routing import AIRouting
from qiskit_ibm_transpiler.ai.collection import CollectLinearFunctions
from qiskit_ibm_transpiler.ai.synthesis import AILinearFunctionSynthesis
from qiskit_ibm_transpiler import generate_ai_pass_manager

ai_pm = PassManager([
    AIRouting(backend=backend, optimization_level=3, layout_mode="optimize", local_mode=True),
    CollectLinearFunctions(),
    AILinearFunctionSynthesis(backend=backend, local_mode=True),
])
hybrid = generate_ai_pass_manager(coupling_map=backend.coupling_map,
    ai_optimization_level=3, optimization_level=3, ai_layout_mode="optimize")""",
                    id="c",
                    norun=True,
                    size=21,
                )
            ],
            [
                A("hl", "c", at="ia2", lines=[7]),
                A("hl", "c", at="col", lines=[8]),
                A("hl", "c", at="syn", lines=[9]),
                A("hl", "c", at="hib", range="11-12"),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Sobre el modo de layout.""",
            [
                T(
                    "Tu circuito debe ejecutarse sí o sí en los qubits físicos 10 a 15, que ya fijaste.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué `layout_mode` usas en `AIRouting`?",
                ["`keep`", "`improve`", "`optimize`"],
                0,
                "Correcto: `keep` respeta el layout dado. Suele dar peores resultados porque tiene menos libertad, pero es lo que necesitas.",
                wrong=[None, "`improve` puede mover los qubits.", "`optimize` ignora tu layout."],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Primero, escribe las tres llamadas que listan los métodos que Qiskit ya trae para Clifford, unitarias y routing. [[n2]]Después, cambia el método de routing de una cuadrícula para quitar CNOT.
             [[n3]]Y por último, escribe tu propio plugin de síntesis de Clifford, que se rinde con más de tres qubits y deja pasar al siguiente método.""",
            [
                Exercise(
                    "p3-plugins/listar-metodos",
                    "Guarda en `clifford_metodos`, `unitaria_metodos` y `routing_metodos` los nombres de los métodos registrados para sintetizar un Clifford, para sintetizar una unitaria y para el routing. Las funciones que los listan ya están importadas.",
                    level=1,
                    id="e1",
                    hidden=True,
                    hints=[
                        "Qiskit guarda los plugins en un registro que se consulta por tipo de objeto o por etapa.",
                        "Las tres funciones importadas devuelven listas de nombres; cada una sirve para una de las tres variables.",
                        "Se llaman con paréntesis: dos reciben un nombre entre comillas (el objeto o la etapa) y una no recibe nada.",
                    ],
                ),
                Exercise(
                    "p3-plugins/routing-method",
                    "Cambia `metodo` por otro método de routing de la lista del ejercicio anterior, para que el circuito aleatorio salga con 55 CNOT o menos sobre la cuadrícula de 3×3. Con `basic` salen 79.",
                    level=2,
                    id="e2",
                    hidden=True,
                    hints=[
                        "`basic` inserta SWAP sin mirar qué puertas vienen después; otros métodos sí lo hacen.",
                        "Elige un nombre de la lista de métodos de routing; uno de ellos, `none`, no sirve porque no enruta.",
                        "Cambia solo la cadena de `metodo` y mira cuántas CNOT imprime.",
                    ],
                ),
                Exercise(
                    "p3-plugins/clifford-plugin",
                    "Completa `MiClifford.run`: recibe en `high_level_object` el `Clifford`; `coupling_map`, `target`, `qubits` y `options` describen el chip y las opciones del método, y este plugin no los usa. "
                    "Si el `Clifford` tiene 3 qubits o menos, devuelve su circuito con `synth_clifford_bm`; si tiene más, devuelve `None` para que el transpilador pruebe el siguiente método. "
                    "Trampa: `None` es la señal de «paso»; no lances un error ni devuelvas un circuito vacío.",
                    level=3,
                    id="e3",
                    hidden=True,
                    hints=[
                        "Un plugin de síntesis recibe el objeto de alto nivel y devuelve un circuito, o `None` si se rinde.",
                        "Dentro de `run`, decide según `high_level_object.num_qubits`.",
                        "`synth_clifford_bm` recibe el Clifford y devuelve su circuito.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "proyecto",
            ("", "Tu proyecto: transpilar la cadena"),
            """Con esto termina la transpilación, y el hito tres de tu proyecto. [[circuito]]Ya tienes el circuito de varios pasos de Trotter de la cadena de espines. [[fez]]Transpílalo para FakeFez, [[niveles]]compara los cuatro niveles de optimización [[prof]]y mide cuánta profundidad añade cada paso. Esa profundidad decidirá cuántos pasos caben cuando ejecutes en hardware real.""",
            [
                Flow(
                    [
                        dict(t="Trotter", s="N pasos · rzz + rx", color="blue"),
                        dict(t="FakeFez", s="cz, rz, sx, x", color="teal"),
                        dict(t="niveles 0-3", s="profundidad", color="gold"),
                    ],
                    id="f",
                    stagger=True,
                ),
                Exercise(
                    "p3-plugins/hito3-transpilado",
                    "`circuito(n, J, h, dt, pasos)` ya construye la cadena de Trotter. Transpílala para `FakeFez` con nivel 3 y `seed_transpiler=1` y devuelve el circuito transpilado. Debe usar solo puertas de `FakeFez` y hacer la misma evolución que la cadena.",
                    level=1,
                    needs="qiskit",
                    id="e1",
                    hidden=True,
                    hints=[
                        "El backend define las puertas y el mapa que puede ejecutar el circuito.",
                        "Antes del `return`, pasa `qc` al gestor de pases del backend falso.",
                        "La forma es `generate_preset_pass_manager(___, backend=___, seed_transpiler=___).run(qc)`.",
                    ],
                ),
                Exercise(
                    "p3-plugins/hito3-niveles",
                    'Completa `profundidades(n, J, h, dt, pasos)`: transpila la misma cadena para `FakeFez` con los niveles 0, 1, 2 y 3, todos con `seed_transpiler=1`. Devuelve un diccionario `{"0": profundidad, ..., "3": profundidad}`.',
                    level=2,
                    needs="qiskit",
                    id="e2",
                    hidden=True,
                    hints=[
                        "Usa una sola semilla para que la comparación sea reproducible.",
                        "El nivel es el primer argumento de `generate_preset_pass_manager`; recórrelos en un bucle.",
                        "La forma es `resultado[str(___)] = generate_preset_pass_manager(___, backend=backend, seed_transpiler=1).run(qc).depth()`.",
                    ],
                ),
                Exercise(
                    "p3-plugins/hito3-presupuesto",
                    "Completa `pasos_max(n, J, h, dt, presupuesto)`: devuelve el mayor número de pasos, de 1 a 10, cuya cadena transpilada para `FakeFez` (nivel 3, `seed_transpiler=1`) no supera `presupuesto` de profundidad, o `0` si no cabe ninguno. La trampa: la profundidad que cuenta es la del circuito transpilado, no la de la cadena lógica.",
                    level=3,
                    needs="qiskit",
                    id="e3",
                    hidden=True,
                    hints=[
                        "El hardware ejecuta el circuito transpilado, y cada `rzz` se convierte en varias puertas.",
                        "Cambia solo la línea que mide `profundidad`: el gestor `pm` ya está creado.",
                        "La forma es `pm.run(cadena(___)).depth()`.",
                    ],
                ),
            ],
            [
                A("item", "f", at="circuito", i=0),
                A("item", "f", at="fez", i=1),
                A("item", "f", at="niveles", i=2),
                A("show", "e1", at="prof"),
                A("show", "e2", at="prof", t=1),
                A("show", "e3", at="prof", t=2),
            ],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma, conectadas con tu proyecto.""",
            [T("Un plugin convierte tu idea en una opción más del transpilador.", "subtitle")],
            ask=reflect(
                "¿Qué ventaja tiene publicar un plugin frente a pasar tu pase suelto a cada colega? ¿Y qué cuesta mantenerlo?",
                "Los pases de IA reducen CNOT, pero son una caja negra. ¿En qué casos los usarías en tu proyecto Ising, y qué comprobarías antes de fiarte?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Hay plugins de etapa, de síntesis unitaria y de alto nivel. [[r2]]Se usan con los argumentos method y hls config. [[r3]]Se crean con una subclase y un entry point.
             [[r4]]Y los pases de IA mejoran routing y síntesis. Con esto termina la transpilación; en la Parte cuatro, las primitivas.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["transpiler-plugins", "create-transpiler-plugin", "ai-transpiler-passes"],
    practice=[
        "Transpila un `efficient_su2(20)` para `FakeSherbrooke` con `routing_method` `sabre`, `lookahead` y `basic`, y compara los SWAP.",
        "Instala `qiskit-ibm-transpiler` y prueba `generate_ai_pass_manager` con el mapa de acoplamiento de `FakeFez`.",
    ],
)

s_cierre, a_cierre = resumen(
    [
        "el routing inserta SWAP para acercar qubits que no son vecinos",
        "cada SWAP se traduce a 3 CX",
        "`seed_transpiler` fija el resultado de un transpilador estocástico",
        "la profundidad transpilada decide cuántos pasos de Trotter caben",
    ]
)
cierre = lesson(
    "p3-cierre",
    "Cierre de la Parte III: repaso y cuántos pasos caben",
    "Un repaso corto de la Parte tres y una pregunta del proyecto Ising: cuántos pasos de Trotter caben en un presupuesto de profundidad.",
    [
        "recordar qué etapa inserta SWAP, cuánto cuesta cada uno y cómo reproducir una transpilación",
        "medir la profundidad transpilada de un circuito de Trotter para `FakeFez` y decidir cuántos pasos caben",
    ],
    [
        beat(
            "repaso1",
            ("", "Repaso: las etapas"),
            """Tres preguntas rápidas de la Parte tres, y después una pregunta del proyecto Ising. La primera, sobre las etapas.""",
            [Flow(ETAPAS, id="f", numbered=True)],
            ask=choice(
                "Una CX actúa sobre dos qubits que el layout colocó lejos uno de otro en el chip. ¿Qué etapa inserta SWAP para acercarlos?",
                ["init", "layout", "routing", "scheduling"],
                2,
                "Correcto: el routing inserta SWAP hasta que los dos qubits son vecinos.",
                wrong=[
                    "Init solo reduce las puertas a una o dos de qubits.",
                    "Layout elige dónde empieza cada qubit; no mueve qubits durante el circuito.",
                    None,
                    "Scheduling calcula tiempos; no cambia la conectividad.",
                ],
            ),
        ),
        beat(
            "repaso2",
            ("", "Repaso: coste de un SWAP"),
            """Segunda pregunta, sobre el coste de esos SWAP.""",
            [T("SWAP = CX · CX · CX", "subtitle")],
            ask=numeric(
                "El routing inserta 5 SWAP y la base del chip solo tiene CX como puerta de dos qubits. ¿Cuántas CX añaden?",
                15,
                "Correcto: cada SWAP se traduce a 3 CX, así que 5 SWAP son 15 CX.",
                tol=0,
                hint="Un SWAP no es una puerta base: se traduce a otras.",
            ),
        ),
        beat(
            "repaso3",
            ("", "Repaso: semilla"),
            """Tercera pregunta, sobre reproducir resultados.""",
            [T("SabreLayout y SabreSwap usan aleatoriedad", "subtitle")],
            ask=choice(
                "Transpilas dos veces el mismo circuito con el nivel 3 y obtienes profundidades distintas. ¿Qué fijas para repetir el resultado?",
                ["`seed_transpiler`", "`shots`", "`optimization_level=0`"],
                0,
                "Correcto: el layout y el routing de Sabre son estocásticos, y `seed_transpiler` fija su semilla.",
                wrong=[
                    None,
                    "`shots` es de las primitivas, no del transpilador.",
                    "Bajar el nivel cambia el circuito; no fija la aleatoriedad.",
                ],
            ),
        ),
        beat(
            "pasos",
            ("", "Tu turno"),
            """Ahora la pregunta del proyecto Ising. [[ej]]Cada paso de Trotter añade profundidad al circuito transpilado, y un chip real solo aguanta cierta profundidad. [[n]]Escribe una función que diga cuántos pasos caben dentro de un presupuesto.""",
            [
                Exercise(
                    "p3-cierre/pasos-maximos",
                    r"Escribe `pasos_max(n, presupuesto)`: `n` es el número de espines y `presupuesto`, la profundidad máxima permitida. `trotter(n, pasos)` ya está escrita. Transpila para `FakeFez()` con el nivel 3 y `seed_transpiler=1` el circuito de `pasos` desde 1 hasta 10, y devuelve el mayor número de pasos cuya profundidad no supera el presupuesto, o 0 si ni siquiera cabe uno. Ojo: cuenta la profundidad del circuito transpilado, no la del abstracto.",
                    level=3,
                    id="e1",
                    hidden=True,
                    hints=[
                        "Necesitas la profundidad transpilada de cada número de pasos antes de poder comparar con el presupuesto.",
                        "Crea el pass manager una sola vez, fuera del bucle, con `generate_preset_pass_manager` y el backend.",
                        "Guarda las profundidades en un diccionario `pasos → profundidad`; el resultado es el mayor `pasos` cuya profundidad cabe, con un valor por defecto de 0.",
                    ],
                )
            ],
            [A("show", "e1", at="ej")],
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen de la parte. [[r1]]El routing inserta SWAP. [[r2]]Cada SWAP cuesta tres CX. [[r3]]Fija seed transpiler para repetir un resultado.
             [[r4]]Y la profundidad transpilada decide cuántos pasos de Trotter caben. Con esto cierras la Parte tres; en la siguiente, las primitivas y la simulación.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[],
    practice=[
        "Repite `pasos_max` con `FakeSherbrooke` y compara con `FakeFez`: ¿cuántos pasos caben en un presupuesto de 150?"
    ],
)

LESSONS = [transpilar, etapas, niveles, target, pass_managers, pases, plugins, cierre]
