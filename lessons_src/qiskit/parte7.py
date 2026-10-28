"""Parte VII · Ejecución avanzada y gestión de trabajos."""

from lib import (
    A,
    Box,
    Circ,
    Code,
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

# ------------------------------------------------------------------ 7.1 Circuitos dinámicos en hardware
s_cierre, a_cierre = resumen(
    [
        "en hardware de IBM solo `if` (con `else`): no `for`, `while` ni `switch`",
        "`MidCircuitMeasure` (`measure_2`) para medir a mitad de circuito",
        "límites: ≤ 32 bits por operando, sin anidar, sin reset ni medición dentro del `if`",
        "con Estimator no: usa Sampler y calcula los valores esperados tú",
    ]
)
dinamicos = lesson(
    "p7-dinamicos",
    "Circuitos dinámicos en hardware",
    "Qué parte del control de flujo admite el hardware de IBM, la medición a mitad de circuito, store, sus límites y cómo estimar valores esperados.",
    [
        "saber qué construcciones dinámicas se ejecutan en los QPUs de IBM",
        "usar `MidCircuitMeasure` para mediciones intermedias",
        "respetar los límites de difusión, operandos y anidamiento",
    ],
    [
        beat(
            "intro",
            ("", "Lo que el hardware admite"),
            """En la Parte dos construiste circuitos dinámicos con if, switch, for y while. En el hardware de IBM, por ahora, solo se ejecuta la instrucción if, con su else.
             [[trade]]Y hay un costo: medir a mitad del circuito y procesar la lógica clásica suele tardar más que una puerta de dos qubits. Ese tiempo extra puede anular la ventaja de un circuito menos profundo.
             [[filtrar]]Para ver qué procesadores admiten circuitos dinámicos, filtra con dynamic circuits igual a True.""",
            [
                Table(
                    ["Construcción", "En QPUs de IBM"],
                    [
                        ["`if_test` / `else`", "✅"],
                        ["`switch`", "❌"],
                        ["`for_loop`", "❌"],
                        ["`while_loop`", "❌"],
                    ],
                    id="t",
                    stagger=True,
                    size=26,
                ),
                Code("service.backends(dynamic_circuits=True)", id="c", hidden=True, norun=True),
            ],
            [
                A("item", "t", at="intro", i=0),
                A("item", "t", at="trade", i=1),
                A("item", "t", at="trade", t=1, i=2),
                A("item", "t", at="trade", t=2, i=3),
                A("show", "c", at="filtrar"),
            ],
        ),
        beat(
            "mid",
            ("", "Medir a mitad del circuito"),
            """Antes había una sola instrucción de medición. Pero una medición intermedia tiene otras necesidades que una final: por ejemplo, su duración importa mucho, porque mientras dura, los demás qubits esperan.
             [[mcm]]Desde la versión cero punto cuarenta y tres del cliente existe MidCircuitMeasure, optimizada para medir a mitad del circuito. Se añade con append.
             [[m2]]Corresponde a la instrucción measure dos del backend, que no todos los procesadores tienen: búscala en supported instructions.
             [[reglas]]Recuerda: hace falta al menos un registro clásico, y Estimator ignora las mediciones.""",
            [
                Code(
                    """from qiskit import QuantumCircuit
from qiskit_ibm_runtime.circuit import MidCircuitMeasure

circ = QuantumCircuit(2, 2)
circ.x(0)
circ.append(MidCircuitMeasure(), [0], [0])
print(circ.count_ops())""",
                    id="c",
                ),
                Out("OrderedDict({'x': 1, 'measure_2': 1})", id="o", hidden=True, check=True),
            ],
            [A("hl", "c", at="mcm", lines=[6]), A("show", "o", at="m2")],
        ),
        beat(
            "store",
            ("", "store en hardware"),
            """Desde la cero punto cuarenta y siete puedes usar store en hardware, para guardar una expresión clásica que reutilizas.
             [[ojo]]Un detalle importante: el valor guardado solo vive en la memoria durante la ejecución. No se copia al resultado. Si guardas un registro en temp, el if funciona como esperas, pero al terminar, temp aparece en cero en los datos que recibes.""",
            [
                Code(
                    """qc.store(temp, creg)
with qc.if_test((temp, 0b001)):   # funciona durante la ejecución
    ...
job.result()[0].data.temp         # ¡vale 0!: no se devuelve""",
                    id="c",
                    norun=True,
                ),
                Box(
                    "warn",
                    "store no se devuelve",
                    T("el registro guardado solo existe durante la ejecución", "body"),
                    id="b",
                    hidden=True,
                ),
            ],
            [A("show", "b", at="ojo")],
        ),
        beat(
            "difusion",
            ("", "Límite de difusiones"),
            """La electrónica de control tiene poca memoria, así que hay un límite de instrucciones if. Lo que cuenta son las difusiones: cada vez que datos de medición nuevos se envían a la lógica de control para evaluar una condición.
             [[ej]]Dos if sobre el mismo registro c cero, sin medir en medio, son una sola difusión. Un if sobre un bit de c uno es otra. En total, cuatro bits difundidos.
             [[cifras]]Como referencia: difundiendo sesenta bits cada vez caben unas trescientas difusiones por trabajo; difundiendo un solo bit, unas dos mil cuatrocientas.""",
            [
                Code(
                    """c0 = ClassicalRegister(3)
c1 = ClassicalRegister(5)
with circuit.if_test((c0, 1)): ...     # difusión 1: 3 bits
with circuit.if_test((c0, 3)): ...     # misma difusión (c0 no cambió)
with circuit.if_test((c1[2], 1)): ...  # difusión 2: 1 bit""",
                    id="c",
                    norun=True,
                ),
                Table(
                    ["bits por difusión", "difusiones por trabajo"],
                    [["60", "≈ 300"], ["1", "≈ 2400"]],
                    id="t",
                    hidden=True,
                    size=26,
                ),
            ],
            [A("hl", "c", at="ej", range="3-5"), A("show", "t", at="cifras")],
        ),
        beat(
            "limites",
            ("", "Otros límites"),
            """Más restricciones. [[bits]]El operando de un if puede tener como máximo treinta y dos bits: no puedes comparar un registro de cincuenta bits completo, pero sí un solo bit de él.
             [[anidar]]No se permiten if anidados. [[dentro]]No se admiten resets ni mediciones dentro de un if. [[arit]]Ni operaciones aritméticas. [[qasm]]Y si envías OpenQASM tres, solo valen instrucciones que Qiskit pueda cargar.""",
            [
                Table(
                    ["Restricción", "Ejemplo"],
                    [
                        [
                            "operando ≤ 32 bits",
                            "`if_test((cr, 15))` con `cr` de 50 bits ❌ · `if_test((cr[5], 1))` ✅",
                        ],
                        ["sin anidar", "`if` dentro de `if` ❌"],
                        ["sin reset ni medición dentro", "`with if_test(...): qc.measure(...)` ❌"],
                        ["sin aritmética", "sumar registros ❌"],
                    ],
                    id="t",
                    stagger=True,
                    size=22,
                )
            ],
            [
                A("item", "t", at="bits", i=0),
                A("item", "t", at="anidar", i=1),
                A("item", "t", at="dentro", i=2),
                A("item", "t", at="arit", i=3),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """¿Se ejecuta en el hardware?""",
            [
                Code(
                    """cr = ClassicalRegister(2)
...
with circuit.if_test((cr, 0b11)):
    circuit.x(q2)""",
                    norun=True,
                )
            ],
            ask=choice(
                "¿Es válido en un QPU de IBM?",
                [
                    "sí: un solo `if` sobre un registro de 2 bits",
                    "no: los registros completos no se pueden comparar",
                    "no: falta un `else`",
                ],
                0,
                "Correcto: es la forma válida de expresar «si los dos bits valen 1» sin anidar dos `if`.",
                wrong=[
                    None,
                    "Sí se puede, mientras el registro tenga ≤ 32 bits.",
                    "El `else` es opcional.",
                ],
            ),
        ),
        beat(
            "pred_correccion",
            ("", "Antes de ejecutar"),
            """Un circuito dinámico clásico: la corrección. Ponemos un qubit en superposición con una Hadamard y lo medimos, y el resultado va al bit cero. [[if]]Si salió uno, aplicamos una X para devolverlo a cero. [[otra]]Y medimos otra vez, ahora en el bit uno.
             [[apuesta]]Apuesta: ¿qué vas a ver en esa segunda medición, la que viene después de la corrección?""",
            [
                Circ(
                    1,
                    [
                        G("h", 0),
                        G("measure", 0, c=0),
                        dict(g="if", q=[0], label="c₀ = 1 ? X", inner="X"),
                        G("measure", 0, c=1),
                    ],
                    clbits=2,
                    creg="c",
                    id="q",
                )
            ],
            ask=predict(
                "¿Qué sale en la segunda medición, tras 1000 disparos?",
                [
                    "`0` siempre",
                    "`1` siempre",
                    "`0` y `1`, cerca de 500 cada uno",
                    "depende de lo que salió en la primera medición",
                ],
                "Anotado. Ejecutémoslo con el simulador Aer, que admite el if, y miremos solo el bit uno.",
            ),
        ),
        beat(
            "correccion",
            ("", "El resultado"),
            """Esto es lo que imprime. [[crudo]]La primera línea tiene los dos bits de cada disparo; el de la derecha es la primera medición. Es aleatoria: la mitad de las veces cero cero y la mitad cero uno.
             [[marg]]La segunda línea, con marginal counts, se queda solo con el bit uno, la segunda medición: mil veces cero. Si apostaste por cero siempre, acertaste.
             [[porque]]Cuando la primera medición dio uno, la X devolvió el qubit a cero; cuando dio cero, ya estaba en cero. Es lo que el hardware calcula en tiempo real, y la razón de ser de los circuitos dinámicos.""",
            [
                Code(
                    """from qiskit import QuantumCircuit
from qiskit.result import marginal_counts
from qiskit_aer import AerSimulator

qc = QuantumCircuit(1, 2)
qc.h(0)
qc.measure(0, 0)
with qc.if_test((qc.clbits[0], 1)):
    qc.x(0)
qc.measure(0, 1)
counts = AerSimulator(seed_simulator=7).run(qc, shots=1000).result().get_counts()
print(counts)
print(marginal_counts(counts, [1]))""",
                    id="c",
                    size=21,
                ),
                Out("{'00': 499, '01': 501}\n{'0': 1000}", id="o", hidden=True, check=True),
            ],
            [
                A("show", "o", at="crudo"),
                A("hl", "c", at="crudo", lines=[12]),
                A("hl", "c", at="marg", lines=[13]),
                A("hl", "c", at="porque", range="8-9"),
            ],
        ),
        beat(
            "estimator",
            ("", "Valores esperados con circuitos dinámicos"),
            """Estimator no admite circuitos dinámicos. Para obtener valores esperados, usa Sampler y haz tú el trabajo de Estimator.
             [[agrupar]]Primero, agrupa los términos de los observables en conjuntos que conmutan qubit a qubit, por ejemplo con PauliList punto group qubit wise commuting.
             [[bases]]Segundo, ejecuta un circuito de cambio de base por grupo. [[sumar]]Tercero, calcula los valores esperados de cada grupo, con BitArray punto expectation values, y súmalos.""",
            [
                Flow(
                    [
                        dict(t="agrupar observables", s="`group_qubit_wise_commuting`"),
                        dict(t="cambio de base", s="un circuito por grupo"),
                        dict(t="Sampler"),
                        dict(t="sumar", s="`BitArray.expectation_values`"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="agrupar", i=0),
                A("item", "f", at="bases", i=1),
                A("item", "f", at="bases", t=1.5, i=2),
                A("item", "f", at="sumar", i=3),
            ],
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Abre el cuaderno de práctica de esta lección. [[n1]]Primero reproduces la corrección que acabamos de ver y compruebas que la segunda medición es siempre cero. [[n2]]Después reemplazas dos if anidados por uno solo sobre un registro de dos bits. [[n3]]Y por último escribes una función que decide si un circuito cumple los límites del hardware.
             [[check]]Busca la marca verde en cada misión.""",
            [
                Mission(
                    "practica/p7-dinamicos.py",
                    [
                        (
                            1,
                            "Mide, corrige con un `if` y comprueba que la segunda medición es siempre `0`.",
                        ),
                        (2, "Reemplaza dos `if` anidados por un único `if_test((cr, 0b11))`."),
                        (
                            3,
                            "Escribe `es_valido(qc)`: rechaza bucles, `switch`, `if` anidados, mediciones dentro de un `if` y operandos de más de 32 bits.",
                        ),
                    ],
                    id="m",
                    stagger=True,
                )
            ],
            [
                A("item", "m", at="n1", i=0),
                A("item", "m", at="n2", i=1),
                A("item", "m", at="n3", i=2),
            ],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda en tu navegador.""",
            [T("Explicar con tus palabras es la mejor prueba de que entendiste.", "subtitle")],
            ask=reflect(
                "La corrección `H · medir · if X` deja el qubit en cero. ¿Qué habría que hacer sin circuitos dinámicos, y qué costo tendría?",
                "Tienes un circuito con tres `if` anidados. ¿Cómo lo reescribirías para que el hardware lo acepte?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]En hardware de IBM, solo if y else. [[r2]]MidCircuitMeasure mide a mitad de circuito con menos sobrecarga. [[r3]]Hay límites de difusiones, de bits por operando y de anidamiento.
             [[r4]]Y para valores esperados con circuitos dinámicos, Sampler más tu propio posprocesamiento.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["execute-dynamic-circuits"],
    practice=[
        "Reescribe con un único `if` y un registro de 2 bits un circuito que tenga dos `if` anidados.",
        "Ejecuta en un QPU el ejemplo de corrección `H · medir · if (c=1) X · medir` y comprueba que sale `0` casi siempre.",
    ],
)

# ------------------------------------------------------------------ 7.2 Puertas fraccionales
ISING = """from qiskit import QuantumCircuit
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import generate_preset_pass_manager

n, steps = 5, 3
ising = QuantumCircuit(n)
for _ in range(steps):
    for q in range(n):
        ising.rx(0.1, q)
    for q in range(1, n - 1, 2):
        ising.rzz(0.1, q, q + 1)
    for q in range(0, n - 1, 2):
        ising.rzz(0.1, q, q + 1)
    ising.barrier()

conventional = GenericBackendV2(n, basis_gates=["cz", "rz", "sx", "x"], seed=1)
fractional = GenericBackendV2(n, basis_gates=["cz", "rz", "sx", "x", "rx", "rzz"], seed=1)
for name, backend in (("convencional", conventional), ("fraccional", fractional)):
    isa = generate_preset_pass_manager(3, backend=backend, scheduling_method="alap").run(ising)
    print(name, isa.count_ops().get("cz", 0), isa.count_ops().get("rzz", 0),
          round(isa.estimate_duration(backend.target, unit="s") * 1e6, 2), "µs")"""
s_cierre, a_cierre = resumen(
    [
        "Heron: $R_X(\\theta)$ con cualquier ángulo y $R_{ZZ}(\\theta)$ con $0<\\theta\\le\\pi/2$",
        "`service.backend(nombre, use_fractional_gates=True)`",
        "menos puertas y menor duración en circuitos con muchas rotaciones",
        "experimental · sin twirling de puertas, PEC ni PEA · Qiskit Pulse fue retirado",
    ]
)
fraccionales = lesson(
    "p7-fraccionales",
    "Puertas fraccionales",
    "Rotaciones RX y RZZ ejecutadas directamente en procesadores Heron: cuándo convienen, cómo activarlas, sus límites, y el reemplazo de Qiskit Pulse.",
    [
        "activar puertas fraccionales en un backend",
        "estimar cuánto acortan un circuito de evolución temporal",
        "conocer sus restricciones y las técnicas incompatibles",
    ],
    [
        beat(
            "que",
            ("", "Rotaciones directas"),
            """Las puertas base de IBM han sido CZ, X, RZ, raíz de X e identidad. Con ellas, una rotación RX de un ángulo cualquiera necesita varias puertas RZ y raíz de X, y una RZZ necesita dos CZ y varias puertas de un qubit.
             [[frac]]Los procesadores Heron admiten dos puertas fraccionales: RX con cualquier ángulo, [[rzz]]y RZZ con ángulos entre cero y pi medios.
             [[ventaja]]Ejecutarlas directamente reduce hasta la mitad la duración y el error de las rotaciones de un qubit, y evita descomponer las RZZ en CZ.""",
            [
                Row(
                    Circ(1, [G("rx", 0, p="θ")], id="a"),
                    T("→", "title"),
                    Circ(
                        1,
                        [
                            G("rz", 0, p="π/2"),
                            G("sx", 0),
                            G("rz", 0, p="θ+π"),
                            G("sx", 0),
                            G("rz", 0, p="5π/2"),
                        ],
                        id="b",
                    ),
                    gap=20,
                ),
                Row(
                    Box(
                        "def", "$R_X(\\theta)$", T("cualquier ángulo", "body"), id="x", hidden=True
                    ),
                    Box(
                        "def",
                        "$R_{ZZ}(\\theta)$",
                        T("$0<\\theta\\le\\pi/2$", "body"),
                        id="z",
                        hidden=True,
                    ),
                    gap=26,
                ),
            ],
            [A("show", "x", at="frac"), A("show", "z", at="rzz")],
        ),
        beat(
            "activar",
            ("", "Activarlas"),
            """Aunque RX y RZZ están en la biblioteca estándar de Qiskit, solo se ejecutan directamente en ciertos procesadores, y hay que pedir el backend con use fractional gates igual a True. Así el Target las incluye y el transpilador puede usarlas.
             [[lista]]service punto backends con use fractional gates lista los que las admiten; desde la cero punto cuarenta y ocho, least busy acepta use fractional gates.
             [[fake]]Los backends falsos las tienen desactivadas por defecto; se activan refrescando su configuración con el servicio.
             [[error]]Un detalle: el error que reporta el Target para las fraccionales es una copia del de la puerta convencional equivalente, porque todavía no se miden por separado.""",
            [
                Code(
                    """backend = service.backend("ibm_kingston", use_fractional_gates=True)
service.backends(use_fractional_gates=True)
service.least_busy(use_fractional_gates=True)      # desde 0.48
fake_backend.refresh(service=service, use_fractional_gates=True)""",
                    id="c",
                    norun=True,
                )
            ],
            [
                A("hl", "c", at="activar", lines=[1]),
                A("hl", "c", at="lista", range="2-3"),
                A("hl", "c", at="fake", lines=[4]),
            ],
        ),
        beat(
            "pred_ising",
            ("", "Antes de transpilar"),
            """Vamos a simular la dinámica de una cadena de Ising con cinco qubits y tres pasos de tiempo. [[paso]]Cada paso aplica una capa de RX y dos capas de RZZ, que en total son cuatro RZZ, una por cada par de vecinos.
             [[cuenta]]Recuerda que, sin puertas fraccionales, cada RZZ se descompone en dos CZ. [[apuesta]]Haz la cuenta y apuesta: ¿cuántas CZ crees que necesitará el backend convencional?""",
            [
                Table(
                    ["Cadena de Ising", ""],
                    [
                        ["qubits", "5"],
                        ["pasos", "3"],
                        ["`rx` por paso", "5"],
                        ["`rzz` por paso", "4"],
                    ],
                    id="t",
                    stagger=True,
                    size=26,
                )
            ],
            [
                A("item", "t", at="paso", i=0),
                A("item", "t", at="paso", t=1, i=1),
                A("item", "t", at="paso", t=2, i=2),
                A("item", "t", at="paso", t=3, i=3),
            ],
            ask=predict(
                "¿Cuántas `cz` necesita el backend convencional?",
                ["12", "24", "36", "ninguna"],
                "Anotado. Transpilemos para los dos backends y miremos.",
            ),
        ),
        beat(
            "ising",
            ("", "Ejemplo: una cadena de Ising"),
            """El ejemplo de la guía simula la dinámica de una cadena de Ising: capas de RX seguidas de capas de RZZ, tres pasos de tiempo, cinco qubits.
             [[comp]]Lo transpilamos para dos backends genéricos, uno sin y otro con puertas fraccionales, y programamos los tiempos para medir la duración.
             [[res]]Sin fraccionales: veinticuatro CZ, dos por cada una de las doce RZZ, y casi nueve microsegundos. Si apostaste por veinticuatro, acertaste. Con fraccionales: doce RZZ, ninguna CZ, y un coma dos microsegundos. Siete veces más corto.""",
            [
                Code(ISING, id="c", size=18),
                Out(
                    "convencional 24 0 8.98 µs\nfraccional 0 12 1.24 µs",
                    id="o",
                    hidden=True,
                    check=True,
                ),
                Hist(
                    [["convencional", 8.98], ["fraccional", 1.24]],
                    id="h",
                    hidden=True,
                    h=120,
                    ymax=10.5,
                    digits=2,
                    ylabel="µs",
                    color="teal",
                ),
            ],
            [
                A("hl", "c", at="ising", range="5-14"),
                A("hl", "c", at="comp", range="16-19"),
                A("show", "o", at="res"),
                A("show", "h", at="res", t=1),
            ],
        ),
        beat(
            "angulos",
            ("", "Restricción de ángulos"),
            """La RZZ solo admite ángulos entre cero y pi medios. Si tu circuito tiene una RZZ fuera de ese rango, el transpilador normalmente la corrige con una transformación equivalente, mediante el pase FoldRzzAngle.
             [[cuando]]¿Dónde conviene usarlas? En circuitos con muchas rotaciones de un qubit o de dos qubits que no son múltiplos de pi medios: ansatz variacionales y simulación de evolución temporal.""",
            [
                M(r"R_{ZZ}(\theta):\ 0<\theta\le\tfrac{\pi}{2}", size=46),
                T("fuera de rango → `FoldRzzAngle` la reescribe", "note", id="n"),
                Box(
                    "idea",
                    "Dónde ayudan",
                    T(
                        "ansatz variacionales · evolución temporal · muchas rotaciones arbitrarias",
                        "body",
                    ),
                    id="b",
                    hidden=True,
                ),
            ],
            [A("show", "b", at="cuando")],
        ),
        beat(
            "cuando_no",
            ("", "Cuándo no usarlas"),
            """Las puertas fraccionales son experimentales: el comportamiento de la opción puede cambiar. [[transp]]El transpilador aún aprovecha poco la RZZ en sus optimizaciones, así que tendrás que cuidar más el diseño del circuito.
             [[incomp]]Y no se pueden combinar con twirling de puertas, aunque sí con el twirling de mediciones de TREX; tampoco con PEC ni con ZNE basada en PEA.""",
            [
                Table(
                    ["Con puertas fraccionales", ""],
                    [
                        ["twirling de puertas", "❌"],
                        ["TREX (twirling de mediciones)", "✅"],
                        ["PEC", "❌"],
                        ["ZNE con PEA", "❌"],
                    ],
                    id="t",
                    stagger=True,
                    size=25,
                )
            ],
            [
                A("item", "t", at="incomp", i=0),
                A("item", "t", at="incomp", t=1.5, i=1),
                A("item", "t", at="incomp", t=3, i=2),
                A("item", "t", at="incomp", t=4, i=3),
            ],
        ),
        beat(
            "pulse",
            ("", "Adiós a Qiskit Pulse"),
            """Con la llegada de las puertas fraccionales, IBM retiró el control a nivel de pulsos en sus procesadores, y el módulo qiskit punto pulse se eliminó en Qiskit dos punto cero.
             [[uso]]El uso más común de los pulsos era justamente construir rotaciones de uno y dos qubits más eficientes, modificando los pulsos ECR o RX. Eso ahora lo cubren las fraccionales.
             [[dyn]]Para todo lo demás, modelar la física del dispositivo, simular programas de pulsos u optimizarlos, está el paquete Qiskit Dynamics, del ecosistema.""",
            [
                Flow(
                    [
                        dict(t="Qiskit Pulse", s="retirado (Qiskit 2.0)", color="red"),
                        dict(t="rotaciones eficientes", s="→ puertas fraccionales", color="teal"),
                        dict(t="física del dispositivo", s="→ Qiskit Dynamics", color="violet"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="pulse", i=0),
                A("item", "f", at="uso", i=1),
                A("item", "f", at="dyn", i=2),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Una pregunta práctica.""",
            [T("Quieres ejecutar un VQE con muchas RX y RZZ y mitigarlo con PEC.", "body")],
            ask=choice(
                "¿Qué haces con las puertas fraccionales?",
                [
                    "las activas: siempre convienen",
                    "no las activas: PEC es incompatible con ellas",
                    "las activas solo para las RZZ",
                ],
                1,
                "Correcto: hay que elegir. O puertas fraccionales (circuito más corto) o PEC; o usar otra mitigación compatible, como TREX.",
                wrong=[
                    "No siempre: PEC no se combina con ellas.",
                    None,
                    "La opción se activa para el backend entero, no por tipo de puerta.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Abre el cuaderno de práctica. [[n1]]Primero reproduces la comparación de la cadena de Ising y ves cuánto acortan las fraccionales. [[n2]]Después cambias el ángulo de las RZZ para que el backend convencional necesite menos CZ. [[n3]]Y por último escribes una función que construye la cadena de Ising con los parámetros que quieras.
             [[check]]Cada misión tiene su comprobación: busca la marca verde.""",
            [
                Mission(
                    "practica/p7-fraccionales.py",
                    [
                        (
                            1,
                            "Transpila la cadena de Ising para los dos backends y cuenta las `cz` y las `rzz`.",
                        ),
                        (
                            2,
                            r"Cambia `theta_zz` por un múltiplo de $\pi/2$ y mira cuántas `cz` necesita el convencional.",
                        ),
                        (
                            3,
                            "Escribe `cadena_ising(n, pasos, theta_x, theta_zz)`; la comprobación cuenta sus puertas.",
                        ),
                    ],
                    id="m",
                    stagger=True,
                )
            ],
            [
                A("item", "m", at="n1", i=0),
                A("item", "m", at="n2", i=1),
                A("item", "m", at="n3", i=2),
            ],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda en tu navegador.""",
            [T("Explicar con tus palabras es la mejor prueba de que entendiste.", "subtitle")],
            ask=reflect(
                "¿Por qué una cadena de Ising se beneficia tanto de `rzz` y `rx` nativas, y qué tipo de circuito casi no ganaría nada?",
                "Quieres mitigar con PEC un circuito de evolución temporal. ¿Qué decisión tomas entre las puertas fraccionales y la mitigación, y por qué?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Heron ejecuta RX y RZZ directamente. [[r2]]Se activan al pedir el backend con use fractional gates. [[r3]]Acortan mucho los circuitos con rotaciones arbitrarias.
             [[r4]]Pero son experimentales, incompatibles con algunas mitigaciones, y reemplazan a Qiskit Pulse.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["fractional-gates", "pulse-migration"],
    practice=[
        "Repite el ejemplo de Ising con 10 qubits y 6 pasos y compara la profundidad de ambos circuitos.",
        "Transpila una RZZ con ángulo $3\\pi/4$ para el backend fraccional y mira cómo la reescribe el transpilador.",
    ],
)

# ------------------------------------------------------------------ 7.3 Temporización
s_cierre, a_cierre = resumen(
    [
        "para circuitos dinámicos, el dibujo de tiempos de Qiskit no es exacto",
        "Sampler: `options.execution.scheduler_timing = True`",
        'metadata `["compilation"]["scheduler_timing"]["timing"]`: rama, instrucción, canal, inicio, duración, pulso',
        "`draw_circuit_schedule_timing` · ese tiempo total **no** es el que se factura",
    ]
)
temporizacion = lesson(
    "p7-temporizacion",
    "Temporización de circuitos",
    "Obtener del servicio la programación real de un circuito, sobre todo dinámico, interpretar sus datos y visualizarla.",
    [
        "pedir los datos de temporización a un trabajo de Sampler",
        "interpretar canales, inicios y duraciones",
        "visualizar la programación con `draw_circuit_schedule_timing`",
    ],
    [
        beat(
            "por_que",
            ("", "Los tiempos reales"),
            """En la Parte dos viste timeline draw, que dibuja los tiempos de un circuito programado. Para circuitos estáticos funciona bien, pero para los dinámicos no es exacto: hay operaciones implícitas, como difundir resultados o decidir una rama, que Qiskit no conoce.
             [[servicio]]Por eso el servicio de IBM puede devolver la programación real que usó. [[exp]]Es una función experimental, solo para trabajos de Sampler.
             [[factura]]Y ojo: el tiempo total de circuito que devuelve no es el que se usa para facturar.""",
            [
                Row(
                    Box("def", "timeline draw (Qiskit)", T("circuitos estáticos", "body")),
                    Box(
                        "idea",
                        "scheduler timing (servicio)",
                        T("también dinámicos · experimental · solo Sampler", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=24,
                ),
                T(
                    "el tiempo de circuito reportado no es el tiempo facturado",
                    "note",
                    id="n",
                    hidden=True,
                    color="red",
                ),
            ],
            [A("show", "b", at="servicio"), A("show", "n", at="factura")],
        ),
        beat(
            "activar",
            ("", "Pedir los datos"),
            """Se activa con una opción experimental del Sampler: en options punto execution, scheduler timing igual a True.
             [[leer]]Después, en la metadata de cada PUB, bajo compilation, scheduler timing, timing, están los datos en bruto.""",
            [
                Code(
                    """from qiskit_ibm_runtime.executor_sampler import Sampler

sampler = Sampler(backend)
sampler.options.execution.scheduler_timing = True
result = sampler.run([isa_circuit]).result()
timing = result[0].metadata["compilation"]["scheduler_timing"]["timing"]""",
                    id="c",
                    norun=True,
                )
            ],
            [A("hl", "c", at="activar", lines=[4]), A("hl", "c", at="leer", lines=[6])],
        ),
        beat(
            "pred_datos",
            ("", "Antes de leerlos"),
            """Vamos a leer los datos de un circuito pequeño: una RZ, una raíz de X y una medición, todas sobre el qubit cero. [[sx]]La raíz de X dura nueve unidades dt. [[m]]La medición, sesenta y cuatro en el canal del qubit. [[rz]]¿Y la RZ? Apuesta antes de verlo.""",
            [
                Table(
                    ["Instrucción", "Duración"],
                    [["`sx`", "9 dt"], ["`measure`", "64 dt"], ["`rz`", "?"]],
                    id="t",
                    stagger=True,
                    size=26,
                )
            ],
            [
                A("item", "t", at="sx", i=0),
                A("item", "t", at="m", i=1),
                A("item", "t", at="rz", i=2),
            ],
            ask=predict(
                "¿Cuánto dura la `rz`?",
                [
                    "0 dt",
                    "9 dt, igual que la `sx`",
                    "64 dt, igual que la medición",
                    "depende del ángulo",
                ],
                "Anotado. Veamos qué dicen los datos.",
            ),
        ),
        beat(
            "datos",
            ("", "Los datos en bruto"),
            """Cada línea describe una instrucción en un canal, con seis campos separados por comas. [[rz]]La primera línea responde la apuesta: la RZ dura cero, porque es un cambio de fase. [[rama]]La rama: main, o la rama then o else de un if. [[instr]]La instrucción y su qubit. [[canal]]El canal: Qubit x, el canal de control del qubit x, o AWGR, el generador de formas de onda de lectura.
             [[t0]]El instante de inicio [[dur]]y la duración, ambos en unidades dt, ciclos de programación; backend punto dt te da su valor en segundos. [[pulso]]Y el tipo de pulso: play aplica un pulso de control; capture registra el estado; shift phase cambia la fase, sin duración, como en las RZ virtuales.""",
            [
                Code(
                    """main,rz_0,Qubit 0,1393,0,shift_phase
main,sx_0,Qubit 0,1393,9,play
main,measure_0,Qubit 0,1402,64,play
main,measure_0,AWGR0_0,1523,325,capture""",
                    "out",
                    id="c",
                ),
                Table(
                    ["Campo", "Ejemplo"],
                    [
                        ["rama", "`main`"],
                        ["instrucción", "`sx_0`"],
                        ["canal", "`Qubit 0` · `AWGR0_0`"],
                        ["inicio", "`1393` dt"],
                        ["duración", "`9` dt"],
                        ["pulso", "`play` · `capture` · `shift_phase`"],
                    ],
                    id="t",
                    stagger=True,
                    size=22,
                ),
            ],
            [
                A("hl", "c", at="rz", lines=[1]),
                A("item", "t", at="rama", i=0),
                A("item", "t", at="instr", i=1),
                A("item", "t", at="canal", i=2),
                A("item", "t", at="t0", i=3),
                A("item", "t", at="dur", i=4),
                A("item", "t", at="pulso", i=5),
            ],
        ),
        beat(
            "dibujar",
            ("", "Visualizarlos"),
            """Desde la cero punto cuarenta y tres, draw circuit schedule timing convierte esos datos en una figura interactiva. Puedes filtrar canales, ocultar los de lectura o las barreras, y guardarla como HTML.
             [[eje]]El eje horizontal es el tiempo en dt; el vertical, los canales. Además de los canales de qubits y de lectura, aparecen el canal de recepción, una instrucción en todos los canales que participan en una comunicación, y el Hub, que controla las difusiones.""",
            [
                Code(
                    """from qiskit_ibm_runtime.visualization import draw_circuit_schedule_timing

fig = draw_circuit_schedule_timing(
    circuit_schedule=timing,
    included_channels=None,
    filter_readout_channels=False,
    filter_barriers=False,
    width=1000,
)
fig.write_html("scheduler_timing.html")""",
                    id="c",
                    norun=True,
                    size=22,
                ),
                T(
                    "canales: `Qubit x` · `AWGRx_y` · Receive channel · Hub (difusiones)",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [A("hl", "c", at="dibujar", range="3-9"), A("show", "n", at="eje")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Interpreta una línea.""",
            [Code("main,sx_0,Qubit 0,1393,9,play", "out")],
            ask=numeric(
                "¿En qué instante (en dt) termina esa puerta SX?",
                1402,
                "Correcto: empieza en 1393 y dura 9 dt, así que termina en 1402, justo cuando empieza la siguiente instrucción del ejemplo.",
                tol=0.0001,
                hint="Inicio + duración.",
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Abre el cuaderno de práctica. [[n1]]Primero escribes un analizador de las líneas de temporización. [[n2]]Después calculas cuándo termina cada instrucción y cuánto dura todo, en nanosegundos. [[n3]]Y por último construyes la programación de un circuito con Qiskit, sin necesidad de un QPU.
             [[check]]Busca la marca verde en cada misión.""",
            [
                Mission(
                    "practica/p7-temporizacion.py",
                    [
                        (1, "Lee las líneas de temporización y conviértelas en tuplas."),
                        (
                            2,
                            "Calcula el fin de cada instrucción y el total en nanosegundos con `backend.dt`.",
                        ),
                        (
                            3,
                            "Escribe `programacion(isa, backend)` con `op_start_times` y las duraciones del `target`.",
                        ),
                    ],
                    id="m",
                    stagger=True,
                )
            ],
            [
                A("item", "m", at="n1", i=0),
                A("item", "m", at="n2", i=1),
                A("item", "m", at="n3", i=2),
            ],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda en tu navegador.""",
            [T("Explicar con tus palabras es la mejor prueba de que entendiste.", "subtitle")],
            ask=reflect(
                "Un colega suma las duraciones del dibujo de tiempos y dice que ese es su costo en QPU. ¿Qué le explicas?",
                "¿Por qué la RZ dura cero y qué otras puertas esperarías que sean «virtuales»?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Para circuitos dinámicos, pide los tiempos al servicio. [[r2]]Se activan con scheduler timing en las opciones de ejecución del Sampler. [[r3]]Cada línea tiene rama, instrucción, canal, inicio, duración y pulso.
             [[r4]]Y draw circuit schedule timing los dibuja; ese tiempo no es el facturado.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["qiskit-runtime-circuit-timing"],
    practice=[
        "Ejecuta un circuito dinámico con `scheduler_timing` en un QPU y busca en la figura el canal Hub durante el `if`.",
        "Convierte las duraciones de dt a nanosegundos usando `backend.dt`.",
    ],
)

# ------------------------------------------------------------------ 7.4 Procesadores
PROPS = """from qiskit_ibm_runtime.fake_provider import FakeFez

backend = FakeFez()
print(backend.name, backend.num_qubits, backend.processor_type)
print(backend.qubit_properties(1))
print(backend.target["measure"][(0,)])
edge = next(iter(backend.target["cz"]))
print(edge, backend.target["cz"][edge])"""
s_cierre, a_cierre = resumen(
    [
        "familias: Nighthawk (cuadrícula, 120 qubits) · Heron (156, heavy hex) · revisiones r1, r2, r3",
        "estático: nombre, versión X.Y.Z, qubits, `processor_type`, `supported_instructions`",
        "dinámico: $T_1$, $T_2$, errores de lectura y de puertas, EPLG, CLOPS · `target`",
        "monitoreo cada hora, calibraciones según deriva, benchmarking diario · `rep_delay`",
    ]
)
procesadores = lesson(
    "p7-procesadores",
    "Los procesadores de IBM",
    "Familias de procesadores, cómo listar backends y leer sus propiedades estáticas y dinámicas, cómo se calibran, la inicialización de qubits y los procesadores retirados.",
    [
        "distinguir las familias Nighthawk y Heron y sus revisiones",
        "consultar propiedades de qubits e instrucciones",
        "entender monitoreo, calibración, benchmarking y `rep_delay`",
    ],
    [
        beat(
            "familias",
            ("", "Familias y revisiones"),
            """Los procesadores de IBM se nombran por familia y revisión. La familia, un nombre de ave, indica el tamaño y la conectividad; la revisión, mejoras de diseño dentro de la familia.
             [[nh]]Nighthawk tiene una topología de cuadrícula y ciento veinte qubits programables; su revisión dos, de septiembre de dos mil veintiséis, añade un reset rápido en cada qubit, que aumenta mucho los circuitos por segundo.
             [[heron]]Heron tiene ciento cincuenta y seis qubits en red heavy hex en sus revisiones dos y tres, con acopladores ajustables y cableado flexible de alta densidad; la revisión tres mejoró coherencia, fidelidad y lectura.
             [[viejas]]Las familias anteriores, Canary, Falcon, Egret, Hummingbird, Osprey y Eagle, ya están retiradas.""",
            [
                Table(
                    ["Familia", "Topología", "Revisiones"],
                    [
                        [
                            "Nighthawk",
                            "cuadrícula · 120 qubits",
                            "r1 (dic 2025) · r2 (sep 2026, reset rápido)",
                        ],
                        ["Heron", "heavy hex · 156 qubits", "r1 (133 q) · r2 (2024) · r3 (2025)"],
                        [
                            "Retiradas",
                            "—",
                            "Canary · Falcon · Egret · Hummingbird · Osprey · Eagle",
                        ],
                    ],
                    id="t",
                    stagger=True,
                    size=23,
                )
            ],
            [
                A("item", "t", at="nh", i=0),
                A("item", "t", at="heron", i=1),
                A("item", "t", at="viejas", i=2),
            ],
        ),
        beat(
            "listar",
            ("", "Listar backends"),
            """Los procesadores en IBM Cloud se llaman ibm guion bajo y el nombre de una ciudad, que no indica dónde está el equipo.
             [[backends]]service punto backends lista los disponibles para ti, con filtros como simulator, operational o min num qubits, [[uno]]backend, en singular, devuelve uno por su nombre, [[least]]y least busy, el que tiene menos trabajos en cola. También se ven en la página Compute resources de la plataforma.""",
            [
                Code(
                    """service.backends(simulator=False, operational=True, min_num_qubits=100)
service.backend("ibm_fez")
service.least_busy(operational=True, min_num_qubits=100)""",
                    id="c",
                    norun=True,
                )
            ],
            [
                A("hl", "c", at="backends", lines=[1]),
                A("hl", "c", at="uno", lines=[2]),
                A("hl", "c", at="least", lines=[3]),
            ],
        ),
        beat(
            "pred_estatica",
            ("", "Antes de mirar"),
            """En un procesador, no todas las operaciones duran lo mismo. [[cz]]Una puerta de dos qubits, la CZ, es de lo más rápido que hace. [[med]]Medir un qubit es más lento, porque hay que leer la señal. [[apuesta]]Vamos a consultar Fez. Antes, apuesta: ¿cuántas veces más dura una medición que una CZ?""",
            [
                Flow(
                    [
                        dict(t="CZ", s="puerta de dos qubits"),
                        dict(t="measure", s="lectura de un qubit"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [A("item", "f", at="cz", i=0), A("item", "f", at="med", i=1)],
            ask=predict(
                "¿Cuántas veces más dura `measure` que `cz`?",
                ["unas 2 veces", "unas 5 veces", "unas 20 veces", "unas 200 veces"],
                "Anotado. Consultemos el target de Fez.",
            ),
        ),
        beat(
            "estatica",
            ("", "Información estática"),
            """Hay información que casi no cambia: nombre, número de qubits, tipo de procesador y versión. [[ej]]Con el backend falso Fez lo vemos sin cuenta: ciento cincuenta y seis qubits, familia Heron, revisión dos.
             [[dur]]Y en las dos últimas líneas está la respuesta a tu apuesta: medir dura uno coma cincuenta y seis microsegundos y la CZ, ochenta y cuatro nanosegundos. Son unas dieciocho veces y media más; si apostaste por veinte, estuviste cerca.
             [[version]]La versión tiene la forma mayor punto menor punto revisión. Un circuito compilado para una versión siempre corre en ella; si cambia solo la revisión, sigue corriendo; si cambia la mayor o la menor, ya no está garantizado.
             [[instr]]Y supported instructions lista las instrucciones nativas: cz, rz, sx, x, id, delay, measure, measure dos, reset, if else y store.""",
            [
                Code(PROPS, id="c", size=21),
                Out(
                    """fake_fez 156 {'family': 'Heron', 'revision': '2'}
QubitProperties(t1=0.0002557051713972407, t2=0.000302790873822133, frequency=None)
InstructionProperties(duration=1.56e-06, error=0.011474609375)
(0, 1) InstructionProperties(duration=8.4e-08, error=0.0101566715843735)""",
                    id="o",
                    hidden=True,
                    check=True,
                    size=17,
                ),
                Table(
                    ["Cambia…", "por ejemplo"],
                    [
                        ["mayor", "cambios de muestra, electrónica, traslado"],
                        ["menor", "ciclos de enfriamiento, quitar una puerta, invertir una CNOT"],
                        ["revisión", "software, calibraciones manuales"],
                    ],
                    id="t",
                    hidden=True,
                    size=21,
                ),
            ],
            [
                A("hl", "c", at="ej", range="3-4"),
                A("show", "o", at="ej", t=2),
                A("show", "t", at="version"),
            ],
        ),
        beat(
            "dinamica",
            ("", "Propiedades que cambian"),
            """Otras propiedades cambian con cada calibración. [[t1]]T uno: cuánto tarda, en promedio, un qubit en decaer de uno a cero. T dos: cuánto mantiene la coherencia de fase de una superposición, medido con un eco de Hahn. En Fez, el qubit uno tiene unos doscientos cincuenta y seis microsegundos de T uno.
             [[lect]]Error de lectura: la media de dos probabilidades, medir cero habiendo preparado uno, y medir uno habiendo preparado cero.
             [[target]]Los errores y duraciones de cada instrucción están en el Target: medir el qubit cero dura un coma cinco seis microsegundos con un uno coma uno por ciento de error; una CZ, ochenta y cuatro nanosegundos y un uno por ciento.
             [[mas]]Y hay métricas globales: el error de dos qubits por capas, EPLG, en una cadena de cien qubits; los circuitos por segundo; y CLOPS, capas por segundo.""",
            [
                Table(
                    ["Propiedad", "Dónde"],
                    [
                        ["$T_1$, $T_2$", "`backend.qubit_properties(q)` · `properties().t1(q)`"],
                        [
                            "error de lectura",
                            "`properties().readout_error(q)` · `prob_meas0_prep1`",
                        ],
                        ["error y duración de puertas", '`backend.target["cz"][(a, b)]`'],
                        [
                            "EPLG (100 qubits) · CLOPS · MCPS",
                            "página del procesador · `configuration().mcps`",
                        ],
                        ["estado y cola", "`backend.status().pending_jobs`"],
                    ],
                    id="t",
                    stagger=True,
                    size=22,
                )
            ],
            [
                A("item", "t", at="t1", i=0),
                A("item", "t", at="lect", i=1),
                A("item", "t", at="target", i=2),
                A("item", "t", at="mas", i=3),
                A("item", "t", at="mas", t=4, i=4),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Sobre versiones.""",
            [
                T(
                    "Compilaste un circuito para la versión 1.3.37 de un QPU. Ahora el QPU está en la versión 1.3.40.",
                    "body",
                )
            ],
            ask=choice(
                "¿Tu circuito sigue garantizado?",
                [
                    "sí: solo cambió la revisión",
                    "no: cambió la versión menor",
                    "no: cambió la versión mayor",
                ],
                0,
                "Correcto: de 1.3.37 a 1.3.40 solo cambia la revisión, que no rompe circuitos compilados.",
                wrong=[None, "La menor sigue siendo 3.", "La mayor sigue siendo 1."],
            ),
        ),
        beat(
            "calibracion",
            ("", "Monitoreo, calibración y benchmarking"),
            """¿Cómo se mantiene estable un procesador? Con tres procesos. [[monitoreo]]Monitoreo: aproximadamente cada hora, trabajos breves intercalados entre los de los usuarios revisan parámetros de lectura, puertas y actividad de defectos TLS, y pruebas globales como estados de Bell.
             [[calib]]Calibración: cuando algo se desvía, se lanzan calibraciones solo de esos qubits o puertas, a lo largo del día. Una calibración no puede correr durante un trabajo o una sesión: en sesiones largas, el equipo puede perder estabilidad.
             [[bench]]Benchmarking: cada día se miden las métricas que ves en Qiskit, con benchmarking aleatorizado, tiempos de coherencia, lectura y fidelidad por capas.""",
            [
                Flow(
                    [
                        dict(t="Monitoreo", s="≈ cada hora", color="blue"),
                        dict(t="Calibración", s="cuando algo deriva", color="gold"),
                        dict(t="Benchmarking", s="diario · métricas públicas", color="teal"),
                    ],
                    id="f",
                    stagger=True,
                ),
                T(
                    "dos trabajos enviados a la vez pueden correr con calibraciones distintas",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("item", "f", at="monitoreo", i=0),
                A("item", "f", at="calib", i=1),
                A("show", "n", at="calib", t=4),
                A("item", "f", at="bench", i=2),
            ],
        ),
        beat(
            "init",
            ("", "Inicialización de qubits"),
            """Antes de cada disparo, el QPU reinicia los qubits a cero; lo controla la opción init qubits. Como el reset no es perfecto, además se espera un tiempo entre circuitos: el rep delay.
             [[defecto]]En la mayoría de los backends vale doscientos cincuenta microsegundos, y se puede cambiar dentro del rango rep delay range, en Fez de cero a quinientos microsegundos.
             [[tradeoff]]Bajarlo reduce el tiempo total de QPU, pero aumenta el error de preparación. [[merge]]Si pones rep delay en cero y desactivas init qubits, los circuitos se encadenan: cada disparo empieza en el estado final del anterior.
             [[orden]]Y no hay garantía sobre el orden en que se ejecutan los circuitos de distintos PUBs.""",
            [
                Code(
                    """backend.default_rep_delay          # 0.00025 s
backend.rep_delay_range            # [0.0, 0.0005]
sampler.options.execution.rep_delay = 0.0005
sampler.options.execution.init_qubits = True""",
                    id="c",
                    setup="from qiskit_ibm_runtime.executor_sampler import Sampler\nfrom qiskit_ibm_runtime.fake_provider import FakeFez\nbackend = FakeFez()\nsampler = Sampler(backend)",
                ),
                Row(
                    Box("def", "rep_delay ↓", T("menos tiempo de QPU", "body")),
                    Box("warn", "rep_delay ↓", T("más error de preparación", "body")),
                    id="r",
                    hidden=True,
                    gap=24,
                ),
            ],
            [
                A("hl", "c", at="defecto", range="1-2"),
                A("show", "r", at="tradeoff"),
                A("hl", "c", at="merge", range="3-4"),
            ],
        ),
        beat(
            "retirados",
            ("", "Procesadores retirados"),
            """Los procesadores se retiran con el tiempo: por ejemplo, Sherbrooke en julio de dos mil veinticinco, Torino en abril de dos mil veintiséis, y Strasbourg y Brussels a fines de abril de dos mil veintiséis. Sus backends falsos siguen disponibles para practicar.
             [[recuperar]]Tus trabajos en procesadores retirados no se pierden: service punto job con el identificador, o service punto jobs filtrando por el nombre del backend, los recuperan.""",
            [
                Table(
                    ["QPU", "Qubits", "Retiro"],
                    [
                        ["ibm_strasbourg", "127", "2026-04-27"],
                        ["ibm_brussels", "127", "2026-04-27"],
                        ["ibm_torino", "133", "2026-04-01"],
                        ["ibm_sherbrooke", "127", "2025-07-31"],
                    ],
                    id="t",
                    size=24,
                ),
                Code(
                    """job = service.job("<id>")
jobs = service.jobs(backend_name="ibm_sherbrooke")""",
                    id="c",
                    hidden=True,
                    norun=True,
                ),
            ],
            [A("show", "c", at="recuperar")],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Sobre la inicialización.""",
            [T("Quieres terminar antes y bajas `rep_delay` al mínimo.", "body")],
            ask=choice(
                "¿Qué precio pagas?",
                ["ninguno", "más error de preparación del estado inicial", "más error en las CZ"],
                1,
                "Correcto: con menos espera, el reset tiene menos tiempo para dejar el qubit en $|0\\rangle$.",
                wrong=[
                    "Siempre hay un compromiso.",
                    None,
                    "Afecta a la preparación, no a las puertas.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Abre el cuaderno de práctica. [[n1]]Primero lees las propiedades de Fez y calculas cuántas veces más dura medir que una CZ. [[n2]]Después buscas el qubit con el T uno más largo. [[n3]]Y por último escribes una función que elige la mejor cadena de qubits, la de menor error total de CZ, para el proyecto de espines.
             [[check]]Busca la marca verde en cada misión.""",
            [
                Mission(
                    "practica/p7-procesadores.py",
                    [
                        (
                            1,
                            "Lee las propiedades de `FakeFez` y calcula la razón entre medir y una `cz`.",
                        ),
                        (2, "Encuentra el qubit con mayor $T_1$."),
                        (
                            3,
                            "Escribe `mejor_cadena(backend, k)`: $k$ qubits acoplados con el menor error total de `cz`.",
                        ),
                    ],
                    id="m",
                    stagger=True,
                )
            ],
            [
                A("item", "m", at="n1", i=0),
                A("item", "m", at="n2", i=1),
                A("item", "m", at="n3", i=2),
            ],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda en tu navegador.""",
            [T("Explicar con tus palabras es la mejor prueba de que entendiste.", "subtitle")],
            ask=reflect(
                "Para tu cadena de espines, ¿qué pesa más al elegir los qubits: el error de las `cz`, el de lectura o el $T_1$? Justifica.",
                "Los datos de calibración cambian cada día. ¿Qué harías para que tu experimento sea comparable entre dos días?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Nighthawk y Heron son las familias actuales. [[r2]]La información estática incluye versión e instrucciones soportadas. [[r3]]Las propiedades dinámicas, T uno, T dos y errores, están en el Target y en properties.
             [[r4]]Y el equipo se monitorea, calibra y mide cada día; rep delay intercambia tiempo por calidad de preparación.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "processor-types",
        "qpu-information",
        "calibration-jobs",
        "repetition-rate-execution",
        "retired-qpus",
    ],
    practice=[
        "Con `FakeFez`, encuentra el qubit con mayor $T_1$ y la arista CZ con menor error.",
        "Compara en la página [Compute resources](https://quantum.cloud.ibm.com/computers) el EPLG de un Nighthawk y de un Heron.",
    ],
)

# ------------------------------------------------------------------ 7.5 Colas, tiempos y costos
s_cierre, a_cierre = resumen(
    [
        "cola: planificador de reparto justo por instancia (ventana móvil de 28 días)",
        "uso: tiempo que el QPU está bloqueado · sesión = tiempo de reloj activo",
        "estimación: $2\\,\\text{s} + (\\text{rep\\_delay} + \\text{circuito})\\times\\text{ejecuciones}$",
        "límites: `max_execution_time` ≤ 3 h, 10 M ejecuciones, 26,8 M instrucciones por qubit",
    ]
)
colas = lesson(
    "p7-colas-costos",
    "Colas, tiempos y costos",
    "Cómo decide el planificador, qué cuenta como uso, cómo estimarlo, cómo reducirlo, el tiempo máximo de ejecución y los límites de cada trabajo.",
    [
        "explicar el planificador de reparto justo",
        "estimar el uso de un trabajo antes de enviarlo",
        "respetar los límites de tiempo y tamaño de los trabajos",
    ],
    [
        beat(
            "fairshare",
            ("", "El planificador de reparto justo"),
            """Cuando envías un trabajo, entra en la cola del procesador junto con los de todos los usuarios. El orden lo decide un planificador de reparto justo, fair share.
             [[instancia]]Su unidad es la instancia: cada una recibe una asignación de tiempo, y se cuenta su uso en una ventana móvil de veintiocho días; en el plan Flex, en cambio, se compara el uso total con la asignación.
             [[como]]Cuando el QPU queda libre, el planificador elige la instancia que menos ha usado en proporción a su asignación. Así nadie monopoliza el equipo: con el doble de minutos asignados, una instancia ejecuta el doble de trabajos.""",
            [
                Flow(
                    [
                        dict(t="cuenta", s="asignación contratada"),
                        dict(t="instancias", s="cada una con su parte"),
                        dict(t="planificador", s="menor uso / asignación primero", color="gold"),
                    ],
                    id="f",
                    stagger=True,
                ),
                T(
                    "ventana móvil de 28 días (Flex: uso total frente a asignación)",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("item", "f", at="fairshare", i=0),
                A("item", "f", at="instancia", i=1),
                A("show", "n", at="instancia", t=3),
                A("item", "f", at="como", i=2),
            ],
        ),
        beat(
            "uso",
            ("", "Qué cuenta como uso"),
            """El uso es el tiempo durante el cual el QPU está bloqueado para tus trabajos. [[job]]En un trabajo suelto, el tiempo bloqueado para ese trabajo. [[batch]]En un lote, la suma de esos tiempos. [[session]]En una sesión, el tiempo de reloj mientras la sesión está activa, se esté ejecutando algo o no, porque el equipo está reservado para ti.
             [[fallos]]Los trabajos fallidos o cancelados: si falló por un error del sistema, no cuentan; si falló por un error tuyo o lo cancelaste, cuenta lo consumido hasta entonces. En sesiones, siempre cuenta el tiempo activo.
             [[ver]]job punto usage, batch punto usage o session punto usage te dicen el consumo real.""",
            [
                Table(
                    ["Modo", "Uso"],
                    [
                        ["Trabajo", "tiempo de QPU bloqueado"],
                        ["Lote", "suma de los tiempos bloqueados"],
                        ["Sesión", "tiempo de reloj activo (aunque esté ocioso)"],
                    ],
                    id="t",
                    stagger=True,
                    size=25,
                ),
                Code("job.usage() · batch.usage() · session.usage()", "text", id="c", hidden=True),
            ],
            [
                A("item", "t", at="job", i=0),
                A("item", "t", at="batch", i=1),
                A("item", "t", at="session", i=2),
                A("show", "c", at="ver"),
            ],
        ),
        beat(
            "estimar",
            ("", "Estimar el uso"),
            """Antes de enviar, puedes aproximar el uso con una fórmula. [[formula]]Unos dos segundos de sobrecarga por subtrabajo, más el rep delay sumado a la duración del circuito, multiplicado por el número de ejecuciones: circuitos por disparos, contando los que genera el broadcasting.
             [[rapido]]Sin mitigación avanzada ni rep delay propio, una regla rápida es dos más cero coma cero cero cero tres cinco por el número de ejecuciones.
             [[ojo]]La mitigación añade circuitos: PEA y PEC, muchos más, por el aprendizaje de ruido.""",
            [
                M(
                    r"\text{uso}\approx 2\,\text{s}+(\text{rep\_delay}+\text{circuito})\times N_{\text{ejecuciones}}",
                    size=34,
                ),
                Box(
                    "warn",
                    "La mitigación añade circuitos",
                    T("PEA y PEC: muchos más, por el aprendizaje de ruido", "body"),
                    id="b",
                    hidden=True,
                ),
            ],
            [A("show", "b", at="ojo")],
        ),
        beat(
            "pred_bell",
            ("", "Antes de calcular"),
            """Pongamos la fórmula a prueba con el circuito más pequeño que conocemos: un estado de Bell, con una Hadamard, una CNOT y la medición. [[disp]]Lo ejecutamos con cuatro mil noventa y seis disparos en Fez, que es un procesador rápido. [[apuesta]]¿Cuántos segundos de QPU crees que usará?""",
            [
                Circ(
                    2,
                    [
                        G("h", 0),
                        G("cx", 0, 1),
                        G("barrier"),
                        G("measure", 0, c=0),
                        G("measure", 1, c=1),
                    ],
                    clbits=2,
                    creg="meas",
                    id="q",
                ),
                T("4096 disparos · FakeFez", "note", id="n", hidden=True),
            ],
            [A("show", "n", at="disp")],
            ask=predict(
                "¿Cuánto uso de QPU estimas para este Bell?",
                ["menos de 1 segundo", "unos 4 segundos", "unos 40 segundos", "unos 4 minutos"],
                "Anotado. Apliquemos la fórmula.",
            ),
        ),
        beat(
            "estimar_ej",
            ("", "Estimar el uso: el cálculo"),
            """[[ej]]Un estado de Bell con cuatro mil noventa y seis disparos en Fez: algo más de tres segundos, que redondeamos hacia arriba a cuatro. Si apostaste por unos cuatro segundos, acertaste. Lo calculamos con la duración del circuito programado y la del reset.
             [[porque]]La sobrecarga de dos segundos pesa el doble que las cuatro mil ejecuciones juntas, que duran cerca de un cuarto de milisegundo cada una.""",
            [
                Code(
                    """import math
from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez

backend = FakeFez()
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()
pm = generate_preset_pass_manager(target=backend.target, optimization_level=0, scheduling_method="alap")
circuit_duration = pm.run(qc).estimate_duration(backend.target, unit="s")
circuit_duration += backend.target["reset"][(0,)].duration + backend.default_rep_delay
print(f"{math.ceil(2 + circuit_duration * 4096)} s")""",
                    id="c",
                    size=20,
                ),
                Out("4 s", id="o", hidden=True, check=True),
            ],
            [A("hl", "c", at="ej", range="12-13"), A("show", "o", at="ej", t=3)],
        ),
        beat(
            "minimizar",
            ("", "Reducir el uso"),
            """Cómo gastar menos. [[shots]]Ejecuta solo los disparos que necesitas: el costo crece con ellos; en Estimator, más precisión significa más disparos.
             [[limites]]Fija límites de tiempo. [[mit]]Usa solo la supresión y mitigación necesarias. [[nl]]Y si repites los mismos circuitos con PEA o PEC, aprende el modelo de ruido una vez y reutilízalo, aunque caduca cuando el equipo deriva.""",
            [
                L(
                    [
                        "solo los disparos necesarios",
                        "límites de tiempo (`max_execution_time`)",
                        "solo la mitigación necesaria",
                        "reutilizar el modelo de ruido aprendido",
                    ],
                    id="l",
                    stagger=True,
                )
            ],
            [
                A("item", "l", at="shots", i=0),
                A("item", "l", at="limites", i=1),
                A("item", "l", at="mit", i=2),
                A("item", "l", at="nl", i=3),
            ],
        ),
        beat(
            "maxtime",
            ("", "Tiempo máximo de ejecución"),
            """El servicio impone un máximo de tres horas por trabajo; si se supera, el trabajo se cancela con RuntimeJobMaxTimeoutError. [[propio]]Puedes fijar uno menor con max execution time, en segundos. Gana el menor de los dos.
             [[qpu]]Ese límite se mide en uso de QPU, no en tiempo de reloj. [[metrics]]Y job punto metrics te dice cuántos segundos cuánticos consumió un trabajo terminado.
             [[ttl]]Lotes y sesiones tienen además un tiempo de vida máximo, el TTL, que verás en la última lección de esta parte.""",
            [
                Code(
                    """estimator.options.max_execution_time = 2500     # segundos de QPU
print(job.metrics()["usage"]["quantum_seconds"])""",
                    id="c",
                    norun=True,
                ),
                T("límite efectivo = min(`max_execution_time`, 3 h)", "note", id="n", hidden=True),
            ],
            [A("show", "n", at="propio"), A("hl", "c", at="metrics", lines=[2])],
        ),
        beat(
            "limites",
            ("", "Límites de cada trabajo"),
            """Antes de entrar en la cola, cada trabajo se valida contra unos límites, para que no falle después de esperar. Se aplican por trabajo, no por PUB, y después de contar lo que añaden opciones como el desacoplamiento dinámico o ZNE.
             [[ejec]]Como máximo diez millones de ejecuciones en Sampler. [[instr]]Hasta veintiséis coma ocho millones de instrucciones de control por qubit, con pesos: una RZ cuenta uno, una SX dos, una CZ cinco, una medición diez, un reset diecisiete.
             [[puertas]]Y por circuito, como máximo treinta millones de RZ, veinte millones de SX y cinco millones de puertas de dos qubits. [[zne]]Ojo con ZNE por plegado: multiplica las puertas de dos qubits por la suma de los factores de ruido.""",
            [
                Table(
                    ["Límite", "Valor"],
                    [
                        ["ejecuciones (Sampler)", "10 millones · circuitos × disparos"],
                        [
                            "instrucciones de control por qubit",
                            "26,8 millones (rz 1 · sx 2 · cz 5 · measure 10 · reset 17)",
                        ],
                        ["por circuito", "30 M RZ · 20 M SX · 5 M de dos qubits"],
                    ],
                    id="t",
                    stagger=True,
                    size=23,
                )
            ],
            [
                A("item", "t", at="ejec", i=0),
                A("item", "t", at="instr", i=1),
                A("item", "t", at="puertas", i=2),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Calcula ejecuciones.""",
            [T("Un PUB con un circuito y parámetros de forma (4, 1), con 2000 disparos.", "body")],
            ask=numeric(
                "¿Cuántas ejecuciones cuenta?",
                8000,
                "Correcto: el broadcasting genera 4 circuitos; 4 × 2000 = 8000 ejecuciones.",
                tol=0.0001,
                hint="Ejecuciones = circuitos (tras el broadcasting) × disparos.",
            ),
        ),
        beat(
            "costo",
            ("", "Ver el costo"),
            """Para ver cuánto has gastado: en la página de instancias, el uso de cada instancia. [[planes]]Su significado depende del plan: en Premium y Open, el uso de los últimos veintiocho días; en Pay As You Go, desde que se creó la instancia; en Flex, desde el inicio del contrato.
             [[trabajo]]Y en la página Workloads, la columna Usage muestra el consumo de cada trabajo.""",
            [
                Table(
                    ["Plan", "«Instance usage» muestra"],
                    [
                        ["Open · Premium", "últimos 28 días"],
                        ["Pay-As-You-Go", "desde la creación de la instancia"],
                        ["Flex", "desde el inicio del contrato"],
                    ],
                    id="t",
                    stagger=True,
                    size=25,
                )
            ],
            [
                A("item", "t", at="planes", i=0),
                A("item", "t", at="planes", t=2, i=1),
                A("item", "t", at="planes", t=4, i=2),
            ],
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Abre el cuaderno de práctica. [[n1]]Primero reproduces la estimación del estado de Bell. [[n2]]Después corriges el conteo de ejecuciones de un PUB con varios valores de parámetro. [[n3]]Y por último conviertes la cuenta en una función, estimar uso, que sirva para cualquier circuito.
             [[check]]Busca la marca verde en cada misión.""",
            [
                Mission(
                    "practica/p7-colas-costos.py",
                    [
                        (1, "Estima el uso de un Bell con 4096 disparos en `FakeFez`."),
                        (
                            2,
                            "Corrige `ejecuciones` para que cuente circuitos × disparos de un PUB.",
                        ),
                        (
                            3,
                            "Escribe `estimar_uso(backend, qc, ejecuciones)` y comprueba varios circuitos.",
                        ),
                    ],
                    id="m",
                    stagger=True,
                )
            ],
            [
                A("item", "m", at="n1", i=0),
                A("item", "m", at="n2", i=1),
                A("item", "m", at="n3", i=2),
            ],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda en tu navegador.""",
            [T("Explicar con tus palabras es la mejor prueba de que entendiste.", "subtitle")],
            ask=reflect(
                "Tu plan Open tiene 10 minutos y un experimento se estima en 30 segundos. ¿Qué otros costos tendrías en cuenta antes de enviarlo?",
                "¿Qué reducirías primero para gastar menos: disparos, circuitos o profundidad? Justifica con la fórmula.",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]El reparto justo ordena la cola por instancia. [[r2]]El uso es tiempo de QPU bloqueado, salvo en sesiones, que cuentan el tiempo activo. [[r3]]Se estima con una fórmula sencilla.
             [[r4]]Y hay límites de tiempo, de ejecuciones y de instrucciones por trabajo.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "fair-share-scheduler",
        "view-cost",
        "estimate-job-run-time",
        "minimize-time",
        "max-execution-time",
        "job-limits",
    ],
    practice=[
        "Estima con la fórmula el uso de un PUB de 10 juegos de parámetros con 4096 disparos y compáralo con `job.usage()` tras ejecutarlo.",
        "Calcula las instrucciones de control por qubit de un GHZ de 50 qubits transpilado para `FakeFez`.",
    ],
)

# ------------------------------------------------------------------ 7.6 Trabajos
s_cierre, a_cierre = resumen(
    [
        "`job.status()`, `job_id()`, `result()`, `wait_for_final_state()`, `cancel()`",
        "«In progress» incluye preprocesamiento clásico y espera del QPU: no es uso",
        "etiquetas: `options.environment.job_tags` · `update_tags` · `service.jobs(job_tags=…)`",
        "recuperar: `service.job(id)`, `service.jobs(...)` · guardar: `RuntimeEncoder` / `RuntimeDecoder`",
    ]
)
trabajos = lesson(
    "p7-trabajos",
    "Monitorear, etiquetar y guardar trabajos",
    "Seguir el estado de un trabajo, entender por qué tarda, cancelarlo, consultar uso y métricas, etiquetarlo y guardar o recuperar sus resultados.",
    [
        "monitorear y cancelar trabajos",
        "organizar trabajos con etiquetas",
        "recuperar resultados y guardarlos en disco",
    ],
    [
        beat(
            "estado",
            ("", "El estado de un trabajo"),
            """Un trabajo pasa por varios estados: pendiente, en curso, completado, fallido o cancelado. [[metodos]]Desde Qiskit: status te da el estado, job id el identificador, result espera y devuelve los resultados, y wait for final state espera sin devolverlos.
             [[recuperar]]Con service punto job y el identificador lo recuperas en cualquier momento, incluso días después.""",
            [
                Table(
                    ["Método", "Para qué"],
                    [
                        ["`job.status()`", "estado actual"],
                        ["`job.job_id()`", "identificador"],
                        ["`job.result()`", "resultados (espera)"],
                        ["`job.wait_for_final_state()`", "esperar a que termine"],
                        ["`job.cancel()`", "cancelar (sin vuelta atrás)"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                )
            ],
            [
                A("item", "t", at="metodos", i=0),
                A("item", "t", at="metodos", t=1, i=1),
                A("item", "t", at="metodos", t=2, i=2),
                A("item", "t", at="metodos", t=3.5, i=3),
                A("item", "t", at="recuperar", i=4),
            ],
        ),
        beat(
            "progreso",
            ("", "¿Por qué sigue «en curso»?"),
            """A veces un trabajo que debería tardar segundos se queda mucho rato en curso. Es normal. [[pre]]Un trabajo pasa a en curso en cuanto empieza su preprocesamiento clásico, no cuando entra al QPU.
             [[paralelo]]Ese preprocesamiento corre en paralelo para varios trabajos, pero el QPU solo ejecuta uno a la vez: esperan su turno. Es la contención del QPU; también ocurre durante una calibración.
             [[uso]]Por eso el tiempo en curso no es tu uso: el uso y el tiempo máximo solo cuentan el tiempo que el QPU está bloqueado para ti. [[sesion]]En una sesión es distinto: durante su ventana activa tienes el equipo en exclusiva.""",
            [
                Flow(
                    [
                        dict(t="pendiente", s="en la cola"),
                        dict(
                            t="en curso", s="preprocesamiento clásico (en paralelo)", color="gold"
                        ),
                        dict(t="espera del QPU", s="contención", color="red"),
                        dict(t="ejecución", s="esto sí es uso", color="teal"),
                        dict(t="completado"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="pre", i=0),
                A("item", "f", at="pre", t=1, i=1),
                A("item", "f", at="paralelo", i=2),
                A("item", "f", at="uso", i=3),
                A("item", "f", at="uso", t=2, i=4),
            ],
        ),
        beat(
            "metricas",
            ("", "Uso y métricas"),
            """service punto usage te dice cuánto te queda en la instancia activa. [[jobs]]service punto jobs, con filtros como created after o session id, lista tus trabajos: puedes sumar su uso, por ejemplo, de los últimos siete días.
             [[props]]Y job punto properties devuelve las propiedades del backend, T uno, T dos o errores de lectura, en el momento en que se ejecutó tu trabajo; también se ven en Workloads, en el historial de calibración.""",
            [
                Code(
                    """from datetime import datetime, timedelta

print(service.usage())
jobs = service.jobs(limit=None, created_after=datetime.now() - timedelta(days=7))
print(sum(job.usage() for job in jobs), "s en 7 días")
properties = job.properties()           # propiedades al ejecutar
print(properties.t1(0), properties.readout_error(0))""",
                    id="c",
                    norun=True,
                    size=22,
                )
            ],
            [
                A("hl", "c", at="metricas", lines=[3]),
                A("hl", "c", at="jobs", range="4-5"),
                A("hl", "c", at="props", range="6-7"),
            ],
        ),
        beat(
            "tags",
            ("", "Etiquetas"),
            """Para organizar experimentos, etiqueta tus trabajos: por ejemplo, con la configuración de mitigación o los parámetros usados. [[asignar]]Se asignan antes de ejecutar, en options punto environment punto job tags.
             [[update]]update tags las cambia después, pero sobrescribe: si quieres añadir una, vuelve a incluir las anteriores. [[buscar]]Y service punto jobs con job tags filtra por ellas.""",
            [
                Code(
                    """sampler.options.environment.job_tags = ["experiment-2025", "sampler-example"]
job = sampler.run([isa_circuit])
job.update_tags(["experiment-2025", "sampler-example", "127-qubit"])   # sobrescribe
service.jobs(job_tags=["experiment-2025", "sampler-example"])""",
                    id="c",
                    norun=True,
                    size=21,
                )
            ],
            [
                A("hl", "c", at="asignar", lines=[1]),
                A("hl", "c", at="update", lines=[3]),
                A("hl", "c", at="buscar", lines=[4]),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Sobre etiquetas.""",
            [
                Code(
                    """# el trabajo tiene ["a", "b"]
job.update_tags(["c"])""",
                    norun=True,
                )
            ],
            ask=choice(
                "¿Qué etiquetas tiene ahora?",
                ["a, b y c", "solo c", "a y b"],
                1,
                'Correcto: `update_tags` sobrescribe. Para añadir, pasa la lista completa: `["a", "b", "c"]`.',
                wrong=[
                    "No se acumulan: se reemplazan.",
                    None,
                    "Sí cambian: se reemplazan por la nueva lista.",
                ],
            ),
        ),
        beat(
            "pred_guardar",
            ("", "Antes de guardar"),
            """Vamos a guardar un resultado en disco y a leerlo de vuelta. [[ida]]Para escribirlo, json punto dump con el codificador RuntimeEncoder. [[vuelta]]Para leerlo, json punto load con el decodificador RuntimeDecoder. [[apuesta]]¿Qué objeto crees que obtendremos al final, y qué pasará con los conteos?""",
            [
                Flow(
                    [
                        dict(t="resultado", s="de un trabajo"),
                        dict(t="json.dump", s="`cls=RuntimeEncoder`"),
                        dict(t="result.json"),
                        dict(t="json.load", s="`cls=RuntimeDecoder`"),
                        dict(t="¿?", color="gold"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="ida", i=0),
                A("item", "f", at="ida", t=1, i=1),
                A("item", "f", at="ida", t=2, i=2),
                A("item", "f", at="vuelta", i=3),
                A("item", "f", at="apuesta", i=4),
            ],
            ask=predict(
                "¿Qué devuelve `json.load(file, cls=RuntimeDecoder)`?",
                [
                    "un diccionario con los conteos",
                    "un `PrimitiveResult` con los mismos conteos",
                    "el texto JSON sin interpretar",
                    "un error: hace falta el servicio",
                ],
                "Anotado. Lo probamos con un resultado local.",
            ),
        ),
        beat(
            "guardar",
            ("", "Recuperar y guardar resultados"),
            """IBM guarda los resultados de todos tus trabajos, así que puedes recuperarlos tras reiniciar Python. [[buscar]]service punto jobs filtra por fecha, backend, estado o sesión, y service punto job recupera uno por su identificador.
             [[disco]]Para guardarlos en disco, usa el módulo json de Python con el codificador RuntimeEncoder, [[leer]]y léelos con RuntimeDecoder. Aquí lo probamos con un resultado local: vuelve a ser un PrimitiveResult con los mismos conteos. Si apostaste por esa opción, acertaste; no hace falta el servicio para leerlo.""",
            [
                Code(
                    """import json
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
from qiskit_ibm_runtime import RuntimeEncoder, RuntimeDecoder

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()
result = StatevectorSampler(seed=3).run([qc]).result()   # o retrieved_job.result()

with open("result.json", "w") as file:
    json.dump(result, file, cls=RuntimeEncoder)
with open("result.json") as file:
    loaded = json.load(file, cls=RuntimeDecoder)
print(type(loaded).__name__, loaded[0].data.meas.get_counts())""",
                    id="c",
                    size=21,
                ),
                Out("PrimitiveResult {'00': 515, '11': 509}", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="buscar", lines=[10]),
                A("hl", "c", at="disco", range="12-13"),
                A("hl", "c", at="leer", range="14-16"),
                A("show", "o", at="leer", t=2),
            ],
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Abre el cuaderno de práctica. [[n1]]Primero guardas un resultado y lo lees de vuelta. [[n2]]Después añades una etiqueta a un trabajo sin perder las que ya tenía. [[n3]]Y por último escribes dos funciones: una que guarda todos los trabajos de una etiqueta, y otra que los carga.
             [[check]]Busca la marca verde en cada misión.""",
            [
                Mission(
                    "practica/p7-trabajos.py",
                    [
                        (
                            1,
                            "Guarda un resultado con `RuntimeEncoder` y léelo con `RuntimeDecoder`.",
                        ),
                        (2, "Añade la etiqueta `c` a un trabajo sin perder `a` y `b`."),
                        (
                            3,
                            "Escribe `guardar_por_etiqueta` y `cargar`, y comprueba que los conteos coinciden.",
                        ),
                    ],
                    id="m",
                    stagger=True,
                )
            ],
            [
                A("item", "m", at="n1", i=0),
                A("item", "m", at="n2", i=1),
                A("item", "m", at="n3", i=2),
            ],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda en tu navegador.""",
            [T("Explicar con tus palabras es la mejor prueba de que entendiste.", "subtitle")],
            ask=reflect(
                "Dentro de un mes quieres encontrar «la ejecución con TREX y 8 pasos de Trotter». ¿Qué etiquetas pondrías hoy?",
                "¿Qué guardarías junto al resultado además de los conteos, para poder repetir el experimento?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]status, result, wait for final state y cancel controlan un trabajo. [[r2]]En curso no es lo mismo que uso: incluye preprocesamiento y espera. [[r3]]Las etiquetas organizan experimentos.
             [[r4]]Y los resultados se recuperan del servicio o se guardan con RuntimeEncoder.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["monitor-job", "add-job-tags", "save-jobs"],
    practice=[
        "Etiqueta tres trabajos con distintas configuraciones de mitigación y recupéralos filtrando por etiqueta.",
        "Guarda el resultado de un trabajo real con `RuntimeEncoder` y cárgalo en otro cuaderno.",
    ],
)

# ------------------------------------------------------------------ 7.7 Modos de ejecución
BATCH_SETUP = """from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeBelemV2

backend = FakeBelemV2()
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()
isa_circuit = generate_preset_pass_manager(backend=backend, optimization_level=1).run(qc)
partitioned_circuits = [[isa_circuit], [isa_circuit]]"""
s_cierre, a_cierre = resumen(
    [
        "job: una petición · batch: trabajos independientes, todos a la vez · session: acceso exclusivo",
        "recomendación: batch por defecto · session solo para cargas iterativas · job para una sola petición",
        "TTL máximo (8 h en planes de pago; lote Open 10 min) e interactivo (1 min lote · 60 s sesión)",
        "en local los modos se ignoran · Open no admite sesiones",
    ]
)
modos = lesson(
    "p7-modos",
    "Modos de ejecución: job, batch y session",
    "Los tres modos de ejecución, cómo elegir, cómo abrir y cerrar lotes y sesiones, sus tiempos de vida, y las preguntas frecuentes.",
    [
        "distinguir los modos job, batch y session",
        "elegir el modo adecuado para cada carga de trabajo",
        "abrir, cerrar y configurar lotes y sesiones",
    ],
    [
        beat(
            "tres",
            ("", "Tres modos"),
            """Los modos de ejecución deciden cómo se programan tus trabajos. [[job]]Job: una sola petición a una primitiva, sin gestor de contexto; mode igual al backend.
             [[batch]]Batch: varios trabajos independientes enviados a la vez. El sistema paraleliza su preprocesamiento clásico y ejecuta las partes cuánticas seguidas. No garantiza el orden ni da acceso exclusivo.
             [[session]]Session: una ventana dedicada para cargas de varios trabajos. Durante ella tienes el equipo en exclusiva; ni siquiera corren calibraciones.
             [[cola]]En lotes y sesiones, el primer trabajo hace la cola normal: con un solo trabajo no ganas nada. Y el plan Open no admite sesiones.""",
            [
                Table(
                    ["Modo", "Qué es", "Acceso"],
                    [
                        ["job", "una petición · `mode=backend`", "compartido"],
                        [
                            "batch",
                            "trabajos independientes, todos a la vez",
                            "compartido · preprocesamiento en paralelo",
                        ],
                        [
                            "session",
                            "ventana dedicada · iterativo",
                            "**exclusivo** · sin calibraciones",
                        ],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                ),
                T(
                    "el primer trabajo siempre hace cola · Open: sin sesiones",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("item", "t", at="job", i=0),
                A("item", "t", at="batch", i=1),
                A("item", "t", at="session", i=2),
                A("show", "n", at="cola"),
            ],
        ),
        beat(
            "ttl",
            ("", "Tiempos de vida"),
            """Lotes y sesiones tienen dos temporizadores. [[max]]El tiempo de vida máximo, TTL, empieza cuando arranca el primer trabajo y no se detiene. Al llegar a su fin, el lote o la sesión termina: lo que se está ejecutando acaba, lo que está en cola falla.
             [[inter]]El TTL interactivo empieza al terminar cada trabajo. Si no llega otro trabajo a tiempo, la carga se desactiva temporalmente y la cola vuelve a la normalidad; un nuevo trabajo puede reactivarla, haciendo cola, mientras no se alcance el máximo.
             [[valores]]Por defecto: máximo de ocho horas en planes de pago, diez minutos para lotes en el plan Open; interactivo de un minuto en lotes y sesenta segundos en sesiones Premium. El interactivo no se puede cambiar; el máximo sí, con max time.""",
            [
                Flow(
                    [
                        dict(t="primer trabajo arranca", s="empieza el TTL máximo", color="blue"),
                        dict(t="trabajo termina", s="empieza el TTL interactivo"),
                        dict(
                            t="¿llega otro a tiempo?",
                            s="no → desactivada temporalmente",
                            color="gold",
                        ),
                        dict(t="TTL máximo", s="fin · la cola falla", color="red"),
                    ],
                    id="f",
                    stagger=True,
                ),
                Table(
                    ["", "TTL máximo", "TTL interactivo"],
                    [
                        ["lote (pago)", "8 h", "1 min"],
                        ["lote (Open)", "10 min", "1 min"],
                        ["sesión (Premium)", "8 h", "60 s"],
                    ],
                    id="t",
                    hidden=True,
                    size=23,
                ),
            ],
            [
                A("item", "f", at="max", i=0),
                A("item", "f", at="inter", i=1),
                A("item", "f", at="inter", t=3, i=2),
                A("item", "f", at="max", t=4, i=3),
                A("show", "t", at="valores"),
            ],
        ),
        beat(
            "elegir",
            ("", "Cómo elegir"),
            """La recomendación general: usa batch, salvo que tu carga no tenga todas las entradas listas al principio. [[batch]]Batch: sin cola extra para cada trabajo, compilación en paralelo, poca deriva entre trabajos, resultados parciales si algo falla, y más barato que una sesión.
             [[session]]Session: todo lo del lote, más acceso exclusivo; ideal para cargas iterativas que necesitan posprocesar antes del siguiente paso, pero más cara, porque cuenta el tiempo activo.
             [[job]]Job: para una sola petición. [[tamano]]Y un consejo: si cada trabajo usa menos de un minuto de QPU, júntalos en uno más grande; hay una sobrecarga fija por trabajo. El preprocesamiento clásico admite hasta cinco trabajos en paralelo.""",
            [
                Table(
                    ["Situación", "Modo"],
                    [
                        ["una sola petición", "job"],
                        ["muchos trabajos independientes", "**batch** (por defecto)"],
                        ["iterativo: optimizador clásico en bucle", "session"],
                        ["trabajos de < 1 min de QPU", "júntalos en uno mayor"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                )
            ],
            [
                A("item", "t", at="job", i=0),
                A("item", "t", at="batch", i=1),
                A("item", "t", at="session", i=2),
                A("item", "t", at="tamano", i=3),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Elige el modo.""",
            [
                T(
                    "Quieres comparar 6 configuraciones de mitigación sobre el mismo circuito; tienes todo listo desde el principio.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué modo usas?",
                ["session", "batch", "seis trabajos sueltos"],
                1,
                "Correcto: son trabajos independientes con todas las entradas listas: un lote los programa juntos, con una sola espera en la cola y poca deriva entre ellos.",
                wrong=[
                    "Una sesión cuesta más y no aporta nada si no hay iteración.",
                    None,
                    "Cada uno haría su propia cola y podrían correr con calibraciones muy distintas.",
                ],
            ),
        ),
        beat(
            "pred_batch",
            ("", "Antes de ejecutar"),
            """Vamos a abrir un lote y a pedirle sus detalles. [[local]]Pero con un backend simulado, en el modo de prueba local, no hay servicio detrás. [[apuesta]]Apuesta: al llamar a details en el lote, ¿qué crees que imprime?""",
            [
                Flow(
                    [
                        dict(t="Batch(backend=...)", s="backend simulado"),
                        dict(t="batch.details()", s="¿qué devuelve?", color="gold"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [A("item", "f", at="local", i=0), A("item", "f", at="apuesta", i=1)],
            ask=predict(
                "¿Qué imprime `print(batch.details())` en modo local?",
                [
                    "un diccionario con el estado y el modo",
                    "`None`",
                    "un error: no hay servicio",
                    "`'batch'`",
                ],
                "Anotado. Ejecutémoslo con `FakeFez`.",
            ),
        ),
        beat(
            "batch",
            ("", "Usar un lote"),
            """Un lote se abre con el gestor de contexto with Batch, pasando el backend; dentro, las primitivas se crean sin modo y lo heredan. [[clase]]O creando un objeto Batch y pasándolo como mode; entonces hay que cerrarlo con close.
             [[cerrar]]Al cerrar, el lote deja de aceptar trabajos, pero los enviados terminan. Si lo dejas abierto y envías más tarde, puede alcanzarse el TTL antes de que corran.
             [[particion]]Un patrón útil: partir una lista larga de circuitos en varios trabajos dentro de un lote, para aprovechar el preprocesamiento en paralelo. [[local]]En el modo de prueba local la sintaxis funciona, pero los modos se ignoran: details imprime None. Si apostaste por eso, acertaste.""",
            [
                Code(
                    """from qiskit_ibm_runtime import Batch
from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.executor_sampler import Sampler

with Batch(backend=backend, max_time="25m"):
    sampler = Sampler()
    jobs = [sampler.run(chunk) for chunk in partitioned_circuits]

batch = Batch(backend=backend)
estimator = Estimator(mode=batch)
...
batch.close()
print(batch.details())""",
                    id="c",
                    size=22,
                    setup=BATCH_SETUP,
                ),
                Out("None", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="batch", range="5-7"),
                A("hl", "c", at="clase", range="9-12"),
                A("hl", "c", at="particion", lines=[7]),
                A("hl", "c", at="local", lines=[13]),
                A("show", "o", at="local"),
            ],
        ),
        beat(
            "session",
            ("", "Usar una sesión"),
            """Con sesiones es igual: with Session, o un objeto Session que se cierra a mano. Si abres una y no envías trabajos en treinta minutos, se cierra sola.
             [[fin]]Una sesión termina al alcanzar el TTL máximo o al cancelarla, y entonces se cancelan los trabajos en cola; o al cerrarla, y entonces los trabajos en cola se ejecutan con prioridad.
             [[estado]]session punto status te dice si está pendiente, aceptando trabajos, sin aceptar trabajos, o cerrada.
             [[vqe]]El uso típico: un optimizador de SciPy que llama a Estimator en cada iteración. Y dentro de una misma sesión puedes ejecutar dos optimizaciones a la vez, con hilos y etiquetas distintas.""",
            [
                Code(
                    """from scipy.optimize import minimize
from qiskit_ibm_runtime import Session
from qiskit_ibm_runtime.executor_estimator import Estimator

with Session(backend=backend) as session:
    estimator = Estimator(options={"default_shots": int(1e4)})
    res = minimize(cost_func, x0, args=(ansatz, hamiltonian, estimator),
                   method="cobyla", options={"maxiter": 25})
    print(session.status())""",
                    id="c",
                    norun=True,
                    size=22,
                ),
                Table(
                    ["Fin de la sesión", "Trabajos en cola"],
                    [
                        ["TTL máximo", "se cancelan"],
                        ["`session.cancel()`", "se cancelan"],
                        ["`session.close()`", "se ejecutan con prioridad"],
                    ],
                    id="t",
                    hidden=True,
                    size=23,
                ),
            ],
            [
                A("hl", "c", at="session", range="5-6"),
                A("show", "t", at="fin"),
                A("hl", "c", at="estado", lines=[9]),
                A("hl", "c", at="vqe", range="7-8"),
            ],
        ),
        beat(
            "faq",
            ("", "Preguntas frecuentes"),
            """Algunas preguntas frecuentes. [[paralelo]]¿Cuántos trabajos corren en paralelo en un lote? Tantos como carriles de ejecución tenga el backend, normalmente cinco, menos los ocupados por otros usuarios.
             [[cola]]¿Los trabajos de un lote esperan cada uno en la cola? No: cuando arranca el primero, los demás pasan a tener prioridad. [[interrup]]¿Las calibraciones interrumpen? Los lotes, sí; las sesiones, no.
             [[usosesion]]¿Una sesión cobra aunque no haga nada? Sí: cuenta desde que arranca el primer trabajo hasta que se desactiva, se cierra o termina el último trabajo, lo que ocurra más tarde. Por eso conviene cerrarlas siempre.""",
            [
                Table(
                    ["Pregunta", "Respuesta"],
                    [
                        [
                            "¿trabajos en paralelo en un lote?",
                            "hasta los carriles libres (normalmente 5)",
                        ],
                        [
                            "¿cada trabajo del lote hace cola?",
                            "no: tras el primero, el resto tiene prioridad",
                        ],
                        ["¿calibraciones durante…?", "lote: sí · sesión: no"],
                        ["¿la sesión cobra aunque esté ociosa?", "sí: cierra siempre tus sesiones"],
                    ],
                    id="t",
                    stagger=True,
                    size=23,
                )
            ],
            [
                A("item", "t", at="paralelo", i=0),
                A("item", "t", at="cola", i=1),
                A("item", "t", at="interrup", i=2),
                A("item", "t", at="usosesion", i=3),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Sobre el cierre.""",
            [T("Terminas de enviar trabajos a una sesión y llamas a `session.close()`.", "body")],
            ask=choice(
                "¿Qué pasa con los trabajos que siguen en cola?",
                ["se cancelan", "se ejecutan con prioridad hasta terminar", "pasan a modo job"],
                1,
                "Correcto: `close()` deja de aceptar trabajos nuevos, pero los pendientes se ejecutan. `cancel()` sí los cancelaría.",
                wrong=["Eso hace `cancel()`.", None, "Siguen siendo de la sesión."],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Abre el cuaderno de práctica. [[n1]]Primero abres un lote, envías tres trabajos y compruebas los conteos. [[n2]]Después partes una lista de veinte circuitos en cinco trabajos. [[n3]]Y por último escribes una función que elige el modo, job, batch o session, según la carga y el plan.
             [[check]]Busca la marca verde en cada misión.""",
            [
                Mission(
                    "practica/p7-modos.py",
                    [
                        (
                            1,
                            "Abre un `Batch`, envía tres trabajos y lee `details()` en modo local.",
                        ),
                        (
                            2,
                            "Reparte 20 circuitos en 5 trabajos de 4, sin perder ni repetir ninguno.",
                        ),
                        (3, "Escribe `elegir_modo(...)` con las recomendaciones de la lección."),
                    ],
                    id="m",
                    stagger=True,
                )
            ],
            [
                A("item", "m", at="n1", i=0),
                A("item", "m", at="n2", i=1),
                A("item", "m", at="n3", i=2),
            ],
        ),
        beat(
            "proyecto",
            ("", "Tu proyecto: hito VII"),
            """El hito siete del proyecto de espines junta lo de esta parte. [[frac]]Primero comparas la cadena de Ising con y sin puertas fraccionales: tus pasos de Trotter son justo rx y rzz.
             [[lote]]Después mides varios pasos de tiempo en un lote, cada uno en su trabajo. [[real]]Y preparas la segunda ejecución real: una guardia estima el uso con la fórmula de la lección siete punto cinco, y solo si el interruptor está encendido y cabe en lo que queda de tu plan Open, deja enviar.
             [[ojo]]El notebook recalcula los resultados de los hitos anteriores, así que no depende de ellos.""",
            [
                Mission(
                    "practica/proyecto/hito7.py",
                    [
                        (
                            1,
                            "Compara la cadena de Trotter en un backend con y sin `rx`/`rzz` nativas.",
                        ),
                        (2, "Mide los pasos 1 a 4 en un `Batch` sobre un backend simulado."),
                        (
                            3,
                            "Escribe la guardia que estima el uso y respeta el presupuesto restante del plan Open.",
                        ),
                    ],
                    title="Proyecto Ising · Hito VII",
                    id="m",
                    hidden=True,
                )
            ],
            [A("show", "m", at="frac")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda en tu navegador.""",
            [T("Explicar con tus palabras es la mejor prueba de que entendiste.", "subtitle")],
            ask=reflect(
                "Para tu proyecto Ising, ¿qué parte pondrías en un lote y cuál en un trabajo suelto? ¿Y si tuvieras un plan de pago?",
                "Antes de gastar minutos del plan Open, ¿qué tres cosas comprobarías?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Job, batch y session. [[r2]]Batch por defecto; session para cargas iterativas; job para una petición. [[r3]]Lotes y sesiones tienen un TTL máximo y otro interactivo.
             [[r4]]En local los modos se ignoran, y el plan Open no admite sesiones. Con esto termina la Parte siete.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "execution-modes",
        "choose-execution-mode",
        "run-jobs-batch",
        "run-jobs-session",
        "execution-modes-faq",
    ],
    practice=[
        "Parte 500 circuitos aleatorios en 5 trabajos y envíalos dentro de un `Batch`; mira `batch.details()`.",
        "Si tienes plan de pago, ejecuta un VQE pequeño en una `Session` y compara su uso con el mismo VQE en modo job.",
    ],
)

LESSONS = [dinamicos, fraccionales, temporizacion, procesadores, colas, trabajos, modos]
