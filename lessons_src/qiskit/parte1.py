"""Parte I · Primeros pasos: qué es Qiskit, patrones, instalación, quickstart y Composer."""

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
    Sh,
    T,
    Table,
    beat,
    choice,
    lesson,
    numeric,
    predict,
    reflect,
    shows,
)
from parte2 import resumen

# ------------------------------------------------------------------ 1.1 Qué es Qiskit
que_es = lesson(
    "p1-que-es-qiskit",
    "Qué es Qiskit",
    "El SDK, el servicio de cómputo de IBM, el ecosistema, los addons, Serverless y Functions: el mapa de todo lo que vas a aprender.",
    [
        "distinguir el SDK de Qiskit del servicio IBM Quantum Compute y del ecosistema",
        "saber qué hace cada módulo principal del SDK",
        "ubicar Serverless, Functions y addons en el panorama",
    ],
    [
        beat(
            "intro",
            ("", "Qiskit no es un solo paquete"),
            """Cuando alguien dice Qiskit, puede referirse a varias cosas. [[col]]Qiskit es un nombre general para una colección de software que sirve para ejecutar programas en computadores cuánticos.
             [[sdk]]En el centro está el SDK, de código abierto, que se instala con el paquete qiskit.
             [[rt]]Luego está el servicio de IBM para ejecutar en sus procesadores cuánticos, que antes se llamaba Qiskit Runtime y hoy se llama IBM Quantum Compute Service.
             [[eco]]Y alrededor hay un ecosistema de proyectos que se conectan con Qiskit sin ser parte de él.""",
            [
                T("¿Qué es Qiskit?", "title"),
                Flow(
                    [
                        dict(t="Qiskit SDK", s="`qiskit` · código abierto", color="blue"),
                        dict(
                            t="IBM Quantum Compute",
                            s="`qiskit-ibm-runtime` · ejecutar en QPUs",
                            color="teal",
                        ),
                        dict(t="Ecosistema", s="Aer, mthree, qBraid…", color="violet"),
                    ],
                    id="f",
                    stagger=True,
                    hidden=True,
                ),
            ],
            [
                A("show", "f", at="col"),
                A("item", "f", at="sdk", i=0),
                A("item", "f", at="rt", i=1),
                A("item", "f", at="eco", i=2),
            ],
        ),
        beat(
            "sdk",
            ("", "Los módulos del SDK"),
            """El SDK trabaja con circuitos extendidos, operadores y primitivas. Tiene cinco piezas que usarás todo el tiempo.
             [[c]]qiskit punto circuit, para construir circuitos: registros, instrucciones, puertas, parámetros y control de flujo.
             [[lib]]La biblioteca de circuitos, con una enorme colección de puertas y circuitos ya hechos.
             [[qi]]quantum info, para trabajar con estados, operadores y canales de forma exacta, sin ruido de muestreo.
             [[tr]]El transpilador, que adapta un circuito a la topología y a las puertas de un dispositivo real, y lo optimiza.
             [[pr]]Y las primitivas, Sampler y Estimator, la forma estándar de ejecutar circuitos.""",
            [
                Table(
                    ["Módulo", "Para qué sirve"],
                    [
                        [
                            "`qiskit.circuit`",
                            "construir circuitos: registros, puertas, parámetros, control de flujo",
                        ],
                        ["`qiskit.circuit.library`", "puertas y circuitos ya hechos"],
                        [
                            "`qiskit.quantum_info`",
                            "estados, operadores y canales de forma **exacta**",
                        ],
                        ["`qiskit.transpiler`", "adaptar y optimizar circuitos para un QPU real"],
                        ["`qiskit.primitives`", "Sampler y Estimator: ejecutar circuitos"],
                    ],
                    id="t",
                    stagger=True,
                )
            ],
            [
                A("item", "t", at="c", i=0),
                A("item", "t", at="lib", i=1),
                A("item", "t", at="qi", i=2),
                A("item", "t", at="tr", i=3),
                A("item", "t", at="pr", i=4),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Una pregunta rápida sobre los módulos.""",
            [
                T(
                    "Quieres calcular el valor esperado exacto de un observable sobre un estado, sin simular mediciones.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué módulo usarías?",
                [
                    "`qiskit.transpiler`",
                    "`qiskit.quantum_info`",
                    "`qiskit.circuit.library`",
                    "`qiskit-ibm-runtime`",
                ],
                1,
                "Correcto: `quantum_info` hace cálculos exactos con estados y operadores, sin ruido de muestreo.",
                wrong=[
                    "El transpilador transforma circuitos; no calcula valores esperados.",
                    None,
                    "La biblioteca ofrece circuitos y puertas, no cálculos con estados.",
                    "Ese paquete envía trabajos a hardware de IBM; aquí basta un cálculo exacto local.",
                ],
            ),
        ),
        beat(
            "ecosistema",
            ("", "Ecosistema, addons y Benchpress"),
            """Fuera del SDK hay proyectos que extienden Qiskit. [[aer]]Qiskit Aer es un paquete de simuladores, con modelos de ruido realistas; lo mantiene IBM.
             [[m3]]mthree implementa una técnica de mitigación de errores de lectura. [[qb]]Y qBraid gestiona trabajos cuánticos en distintas plataformas.
             [[add]]Los addons de Qiskit son otra cosa: herramientas de investigación, modulares, para diseñar algoritmos a escala de utilidad.
             [[bp]]Y para comparar el rendimiento del software, IBM publica Benchpress, el paquete con más de mil pruebas que usa para medir el SDK.""",
            [
                Row(
                    Box(
                        "def",
                        "Ecosistema",
                        L(
                            [
                                "**Qiskit Aer** · simuladores con ruido",
                                "**mthree** · mitigación de lectura",
                                "**qBraid** · gestión de trabajos",
                            ],
                            size=27,
                        ),
                        id="e",
                        hidden=True,
                    ),
                    Box(
                        "idea",
                        "Además",
                        L(
                            [
                                "**Addons** · investigación a escala de utilidad",
                                "**Benchpress** · más de 1000 pruebas de rendimiento",
                            ],
                            size=27,
                        ),
                        id="a",
                        hidden=True,
                    ),
                    gap=30,
                )
            ],
            [A("show", "e", at="aer"), A("show", "a", at="add")],
        ),
        beat(
            "pred_modos",
            ("", "Antes de seguir"),
            """Antes de ver el servicio, una apuesta. IBM ofrece tres maneras de enviar trabajo: un trabajo suelto, una sesión, para cargas iterativas, y un lote, para enviar todo de una vez.
             [[cual]]Una de ellas no está disponible con el plan gratuito, el plan Open. ¿Cuál crees que es?""",
            [
                Flow(["Job", "Session", "Batch"], id="m"),
                T("plan Open: el gratuito", "note", id="n", hidden=True),
            ],
            [A("show", "n", at="cual")],
            ask=predict(
                "¿Qué modo de ejecución no puedes usar con el plan Open?",
                [
                    "el trabajo suelto (`job`)",
                    "la sesión (`session`)",
                    "el lote (`batch`)",
                    "ninguno: con el plan Open puedo usar los tres",
                ],
                "Anotado. Veamos qué dice el servicio.",
            ),
        ),
        beat(
            "servicio",
            ("", "IBM Quantum Compute Service"),
            """El servicio de cómputo de IBM ejecuta tus circuitos en sus procesadores cuánticos, en la nube. [[cli]]Tu programa habla con él a través del paquete qiskit ibm runtime.
             [[mas]]No solo ejecuta: añade recursos clásicos y cuánticos para devolver mejores resultados, con supresión de errores, como el desacoplamiento dinámico, y mitigación, como la extrapolación a ruido cero.
             [[modos]]Y ofrece tres modos de ejecución: un trabajo suelto, una sesión para cargas iterativas, o un lote para enviar todo de una vez.
             [[open]]Ojo: con el plan Open, el gratuito, no se pueden usar sesiones. Si apostaste por la sesión, acertaste.""",
            [
                Code("pip install qiskit-ibm-runtime", "sh", id="c", hidden=True),
                Row(
                    Box("def", "Supresión", T("desacoplamiento dinámico…", "body")),
                    Box("def", "Mitigación", T("lectura (TREX), ZNE…", "body")),
                    id="r",
                    hidden=True,
                    gap=26,
                ),
                Flow(["Job", "Session", "Batch"], id="m", hidden=True),
                T("Plan Open: sin sesiones", "note", id="o", hidden=True, color="red"),
            ],
            [
                A("show", "c", at="cli"),
                A("show", "r", at="mas"),
                A("show", "m", at="modos"),
                A("show", "o", at="open"),
            ],
        ),
        beat(
            "abierto",
            ("", "¿Es de código abierto?"),
            """¿Es todo esto de código abierto? No todo. [[no]]El software que, en los servidores de IBM, se encarga de ejecutar tu programa en el dispositivo, incluida la mitigación de errores, es cerrado.
             [[si]]Pero el cliente, qiskit ibm runtime, el SDK que corre en el servidor y parte del software de mitigación sí son abiertos.
             [[plat]]Todo se administra desde IBM Quantum Platform: usuarios, planes, trabajos. [[crn]]Para ejecutar creas una instancia, y cada instancia tiene un identificador, el CRN, que necesitas para enviar trabajos.""",
            [
                Row(
                    Box(
                        "warn",
                        "Cerrado",
                        T("la ejecución en el QPU y su mitigación de errores", "body"),
                    ),
                    Box(
                        "def",
                        "Abierto",
                        T(
                            "`qiskit-ibm-runtime`, el SDK del servidor, parte de la mitigación",
                            "body",
                        ),
                        id="s",
                        hidden=True,
                    ),
                    gap=26,
                    id="r",
                    hidden=True,
                ),
                Box(
                    "idea",
                    "IBM Quantum Platform",
                    T(
                        "usuarios, planes, trabajos · cada **instancia** tiene un **CRN** (Cloud Resource Name)",
                        "body",
                    ),
                    id="p",
                    hidden=True,
                ),
            ],
            [
                A("show", "r", at="no"),
                A("show", "s", at="si"),
                A("show", "p", at="plat"),
                A("emph", "p", at="crn"),
            ],
        ),
        beat(
            "serverless",
            ("", "Serverless y Functions"),
            """Dos servicios más. [[sl]]Qiskit Serverless ejecuta cargas de trabajo que mezclan recursos clásicos y cuánticos: paraleliza el pre y el posprocesamiento, mantiene trabajos largos en la nube aunque apagues tu laptop, y despliega programas reutilizables.
             [[fn]]Y las Qiskit Functions son servicios ya armados. [[cf]]Las funciones de circuito reciben circuitos abstractos y observables, y se encargan de transpilar, suprimir y mitigar errores.
             [[af]]Las funciones de aplicación cubren el flujo entero, con entradas y salidas del dominio, como un problema de optimización.
             [[planes]]Están disponibles para los planes Premium, Flex y On-Prem.""",
            [
                Row(
                    Box(
                        "def",
                        "Qiskit Serverless",
                        L(
                            [
                                "paralelizar tareas clásicas",
                                "trabajos largos en la nube",
                                "programas reutilizables",
                            ],
                            size=26,
                        ),
                    ),
                    Box(
                        "idea",
                        "Qiskit Functions",
                        L(
                            [
                                "**de circuito**: circuitos + observables → resultados mitigados",
                                "**de aplicación**: problema del dominio → solución",
                            ],
                            size=26,
                            id="l",
                            stagger=True,
                        ),
                        id="f",
                        hidden=True,
                    ),
                    gap=26,
                    id="r",
                    hidden=True,
                ),
                Code(
                    "pip install qiskit_serverless\npip install qiskit-ibm-catalog",
                    "sh",
                    id="c",
                    hidden=True,
                ),
                T("Functions: planes Premium, Flex y On-Prem", "note", id="p", hidden=True),
            ],
            [
                A("show", "r", at="sl"),
                A("show", "f", at="fn"),
                A("item", "l", at="cf", i=0),
                A("item", "l", at="af", i=1),
                A("show", "c", at="af", t=1.5),
                A("show", "p", at="planes"),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Una pregunta para ordenar el mapa.""",
            [
                T(
                    "Solo quieres simular circuitos pequeños en tu computadora, sin cuenta de IBM.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué necesitas instalar como mínimo?",
                [
                    "`qiskit`",
                    "`qiskit` y `qiskit-ibm-runtime`",
                    "`qiskit-ibm-catalog`",
                    "`qiskit_serverless`",
                ],
                0,
                "Correcto: el SDK trae simuladores exactos (las primitivas de referencia). El cliente de IBM solo hace falta para usar sus QPUs.",
                wrong=[
                    None,
                    "El cliente de IBM no hace falta para simular localmente.",
                    "El catálogo es para Qiskit Functions, que corren en la nube de IBM.",
                    "Serverless es para cargas remotas en IBM Quantum Platform.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. Abre el cuaderno de práctica de esta lección con el comando de abajo. [[n1]]Primero reproduces un estado de Bell pasando por cuatro módulos del SDK. [[n2]]Después cambias un observable y calculas su valor exacto, sin simular mediciones.
             [[n3]]Y por último escribes tu propia función de valor esperado, y la comparas con la primitiva del SDK. [[check]]Cada misión tiene una comprobación que se actualiza sola: busca la marca verde.""",
            [
                Mission(
                    "practica/p1-que-es-qiskit.py",
                    [
                        (
                            1,
                            "Pasa un estado de Bell por `circuit`, `quantum_info`, `transpiler` y `primitives`.",
                        ),
                        (
                            2,
                            "Cambia el observable para medir solo la $Z$ del qubit 0 y comprueba su valor exacto.",
                        ),
                        (
                            3,
                            "Escribe `valor_esperado(qc, obs)` con `quantum_info` y compárala con `StatevectorEstimator`.",
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
            """Antes de cerrar, dos preguntas para pensar. No hay respuesta automática: escribe con tus palabras. Lo que escribas se guarda y lo verás cuando vuelvas a esta lección.""",
            [T("Explicar con tus palabras es la mejor prueba de que entendiste.", "subtitle")],
            ask=reflect(
                "Explica con tus palabras la diferencia entre el SDK `qiskit` y el servicio IBM Quantum Compute. ¿Qué instalarías para cada uno?",
                "Piensa en un problema que te interese, como química u optimización. ¿Qué parte del mapa usarías: solo el SDK, un addon o una Function? ¿Por qué?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]El SDK, de código abierto, construye, transforma y ejecuta circuitos. [[r2]]IBM Quantum Compute Service ejecuta en hardware real, con mitigación de errores y tres modos de ejecución.
             [[r3]]El ecosistema y los addons amplían lo que puedes hacer. [[r4]]Y Serverless y Functions llevan flujos completos a la nube.
             En la próxima lección veremos el flujo de trabajo que une todas estas piezas.""",
            [
                L(
                    [
                        "**SDK** `qiskit`: circuit, library, quantum_info, transpiler, primitives",
                        "**IBM Quantum Compute**: QPUs, supresión y mitigación, job · session · batch",
                        "**Ecosistema y addons**: Aer, mthree, herramientas de investigación",
                        "**Serverless** y **Functions**: flujos en la nube",
                    ],
                    id="r",
                    stagger=True,
                )
            ],
            [
                A("item", "r", at="r1", i=0),
                A("item", "r", at="r2", i=1),
                A("item", "r", at="r3", i=2),
                A("item", "r", at="r4", i=3),
            ],
        ),
    ],
    sources=["index", "tools-intro", "compute-services"],
    practice=[
        "Explora el catálogo del ecosistema en [qiskit.github.io/ecosystem](https://qiskit.github.io/ecosystem/) y elige un proyecto que te interese.",
        "Lee los principios de computación cuántica responsable de IBM ([Responsible quantum computing](https://quantum.cloud.ibm.com/docs/en/responsible-quantum-computing)).",
    ],
)

# ------------------------------------------------------------------ 1.2 Patrones
PATRON = Code(
    """
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeBelemV2
from qiskit_ibm_runtime.executor_estimator import Estimator

# 1. Mapear: circuito y observable
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
obs = SparsePauliOp(["ZZ", "XX"])

# 2. Optimizar para el hardware
backend = FakeBelemV2()
pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
isa = pm.run(qc)
isa_obs = obs.apply_layout(isa.layout)

# 3. Ejecutar
estimator = Estimator(mode=backend)
result = estimator.run([(isa, isa_obs)]).result()

# 4. Posprocesar
print(result[0].data.evs)
""",
    id="c",
    size=21,
)

patrones = lesson(
    "p1-patrones",
    "El flujo de trabajo: patrones de Qiskit",
    "Mapear, optimizar, ejecutar y posprocesar: los cuatro pasos de todo programa cuántico, con un ejemplo completo.",
    [
        "describir los cuatro pasos de un patrón de Qiskit",
        "explicar qué es un circuito ISA y por qué es obligatorio en hardware de IBM",
        "elegir entre Sampler y Estimator según lo que quieras obtener",
    ],
    [
        beat(
            "intro",
            ("", "Cuatro pasos"),
            """Todo programa que corre en un computador cuántico, desde un ejemplo de juguete hasta un experimento a gran escala, sigue los mismos cuatro pasos. A esa receta se le llama un patrón de Qiskit.
             [[m]]Mapear el problema a circuitos y operadores. [[o]]Optimizarlos para el hardware. [[e]]Ejecutarlos. [[p]]Y posprocesar los resultados.
             [[het]]Cada paso lo cumplen bloques de software, y el patrón puede correr en tu computadora, en la nube o desplegado con Qiskit Serverless.""",
            [
                T("Un patrón de Qiskit", "title"),
                Flow(
                    [
                        dict(t="Mapear", s="problema → circuitos y operadores", color="blue"),
                        dict(t="Optimizar", s="circuitos → circuitos ISA", color="teal"),
                        dict(t="Ejecutar", s="Sampler o Estimator", color="gold"),
                        dict(t="Posprocesar", s="resultados → respuesta", color="violet"),
                    ],
                    id="f",
                    stagger=True,
                    numbered=True,
                ),
                T("local · nube · Qiskit Serverless", "note", id="n", hidden=True),
            ],
            [
                A("item", "f", at="m", i=0),
                A("item", "f", at="o", i=1),
                A("item", "f", at="e", i=2),
                A("item", "f", at="p", i=3),
                A("show", "n", at="het"),
            ],
        ),
        beat(
            "mapear",
            ("", "1 · Mapear"),
            """El primer paso parte de un problema clásico y lo traduce al lenguaje del computador cuántico. [[quim]]En química o en simulación cuántica, por ejemplo, se construye un circuito que representa el hamiltoniano que quieres estudiar.
             [[topo]]A veces conviene pensar desde ya en cómo se acomodará el problema sobre los qubits del chip, la red heavy hex de IBM, si la estructura del problema lo permite.
             [[prim]]Y conviene decidir ya qué resultado quieres: si necesitas muestras de bits, usarás Sampler; si quieres valores esperados de observables, Estimator, que además ofrece más opciones de mitigación.
             [[sal]]La salida de este paso es una colección de circuitos u operadores.""",
            [
                Flow(
                    [
                        dict(t="Problema", s="molécula, grafo, finanzas…"),
                        dict(t="Circuitos", s="+ observables"),
                    ],
                    id="f",
                ),
                Row(
                    Box("def", "¿Muestras de bits?", T("→ **Sampler**", "body")),
                    Box("def", "¿Valores esperados?", T("→ **Estimator**", "body")),
                    id="r",
                    hidden=True,
                    gap=26,
                ),
                T(
                    "pensar en la red **heavy hex** del chip desde el principio, si ayuda",
                    "note",
                    id="h",
                    hidden=True,
                ),
            ],
            [A("step", "f", at="quim", i=1), A("show", "h", at="topo"), A("show", "r", at="prim")],
        ),
        beat(
            "optimizar",
            ("", "2 · Optimizar"),
            """En el segundo paso, los circuitos abstractos se transforman para el hardware. [[isa]]El resultado debe ser un circuito ISA, por las siglas de arquitectura del conjunto de instrucciones.
             [[base]]Un circuito ISA solo usa las puertas que el hardware entiende, sus puertas base, [[mapa]]y sus puertas de dos qubits respetan la conectividad del chip, el mapa de acoplamiento.
             [[ej]]Mira este estado de Bell. En el procesador Fez, la Hadamard y la CNOT se reescriben con rotaciones Z, raíz de X y una CZ.
             [[solo]]Solo los circuitos ISA se pueden ejecutar en el hardware de IBM. Antes de ejecutar, también conviene probarlos en un simulador.""",
            [
                Row(
                    Circ(2, [G("h", 0), G("cx", 0, 1)], id="a"),
                    T("↓", "title", id="ar", hidden=True),
                    gap=24,
                ),
                Circ(
                    2,
                    [
                        G("rz", 0, p="π/2"),
                        G("sx", 0),
                        G("rz", 0, p="π/2"),
                        G("rz", 1, p="π/2"),
                        G("sx", 1),
                        G("rz", 1, p="π/2"),
                        G("cz", 0, 1),
                        G("rz", 1, p="π/2"),
                        G("sx", 1),
                        G("rz", 1, p="π/2"),
                    ],
                    id="b",
                    hidden=True,
                    scale=1.1,
                ),
                Row(
                    Box(
                        "def",
                        "Puertas base de Fez",
                        T("`rz` · `sx` · `x` · `cz` (+ medición, reset, delay…)", "body"),
                        id="pb",
                        hidden=True,
                    ),
                    Box(
                        "def",
                        "Mapa de acoplamiento",
                        T("CZ solo entre qubits vecinos", "body"),
                        id="ma",
                        hidden=True,
                    ),
                    gap=26,
                ),
            ],
            [
                A("show", "pb", at="base"),
                A("show", "ma", at="mapa"),
                A("show", "ar", at="ej"),
                A("show", "b", at="ej", t=0.4),
            ],
        ),
        beat(
            "ejecutar",
            ("", "3 · Ejecutar"),
            """El tercer paso ejecuta los circuitos ISA con una primitiva: Sampler o Estimator, del paquete qiskit ibm runtime.
             [[modos]]Puedes enviarlos en un lote, que permite transpilar en paralelo, o en una sesión, que sirve para tareas iterativas sin esperar en la cola cada vez.
             [[mit]]Aquí también eliges opciones de supresión y mitigación de errores.
             [[sal]]La salida depende de la primitiva. [[s]]Sampler devuelve los bits medidos en cada disparo. [[e]]Estimator devuelve valores esperados de observables: cantidades físicas o funciones de costo.""",
            [
                Row(
                    Box("def", "Lote · Batch", T("trabajos independientes, en paralelo", "body")),
                    Box(
                        "def",
                        "Sesión · Session",
                        T("tareas iterativas, sin volver a la cola", "body"),
                    ),
                    id="r",
                    hidden=True,
                    gap=26,
                ),
                T("+ opciones de supresión y mitigación", "note", id="m", hidden=True),
                Row(
                    Box("idea", "Sampler", Code("0110  1001  0110  …", "out")),
                    Box("idea", "Estimator", M(r"\langle O\rangle = 0.93 \pm 0.02", size=36)),
                    id="o",
                    hidden=True,
                    gap=26,
                ),
            ],
            [A("show", "r", at="modos"), A("show", "m", at="mit"), A("show", "o", at="sal")],
        ),
        beat(
            "posprocesar",
            ("", "4 · Posprocesar"),
            """El último paso convierte las salidas en la respuesta al problema original. [[vis]]Puede ser algo tan simple como visualizar los resultados.
             [[mit]]O aplicar mitigación de errores de lectura, [[marg]]marginalizar las distribuciones para quedarte con unos pocos qubits, [[ps]]o descartar los resultados que violan una propiedad física del problema, como el número de partículas o la paridad. Eso se llama postselección.""",
            [
                L(
                    [
                        "visualizar",
                        "mitigar errores de lectura",
                        "marginalizar a menos qubits",
                        "postseleccionar: descartar lo que viola una simetría",
                    ],
                    id="l",
                    stagger=True,
                )
            ],
            [
                A("item", "l", at="vis", i=0),
                A("item", "l", at="mit", i=1),
                A("item", "l", at="marg", i=2),
                A("item", "l", at="ps", i=3),
            ],
        ),
        beat(
            "ejemplo",
            ("", "Los cuatro pasos en código"),
            """Así se ven los cuatro pasos en un programa completo, usando un backend falso de cinco qubits, que imita al procesador Belem y corre en tu computadora.
             [[m]]Mapear: un circuito de Bell y un observable, ZZ más XX. [[o]]Optimizar: un pass manager preparado para el backend produce el circuito ISA, [[lay]]y el observable se reacomoda a los qubits físicos con apply layout.
             [[e]]Ejecutar: Estimator, con el backend como modo. [[p]]Posprocesar: leer el valor esperado.""",
            [PATRON],
            [
                A("hl", "c", at="m", range="7-11", dim=True),
                A("hl", "c", at="o", range="13-16", dim=True),
                A("hl", "c", at="lay", lines=[17], dim=True),
                A("hl", "c", at="e", range="19-21", dim=True),
                A("hl", "c", at="p", range="23-24", dim=True),
            ],
        ),
        beat(
            "predice",
            ("", "Antes de ejecutar"),
            """Antes de ejecutarlo, apuesta. Para un estado de Bell ideal, ZZ vale uno y XX también vale uno: la suma ideal es dos.
             [[cual]]Pero el backend falso incluye un modelo del ruido de un procesador real. ¿Qué crees que imprimirá el programa?""",
            [M(r"\langle ZZ\rangle+\langle XX\rangle = 1+1 = 2 \quad\text{(ideal)}", size=40)],
            ask=predict(
                "¿Qué valor esperas para la suma, con el ruido del backend falso?",
                ["exactamente 2", "un poco menos de 2, cerca de 1,9", "cerca de 1", "cerca de 0"],
                "Anotado. Ejecutémoslo y veamos si acertaste.",
            ),
        ),
        beat(
            "resultado",
            ("", "El resultado"),
            """Para un estado de Bell ideal, ZZ vale uno y XX también vale uno: la suma debería dar exactamente dos.
             [[sal]]El backend falso incluye un modelo del ruido del procesador real, así que obtenemos un poco menos, alrededor de uno coma nueve. Si apostaste por esa opción, acertaste.
             [[mens]]Esa diferencia es el ruido, y buena parte del curso trata de cómo reducirla.""",
            [
                M(r"\langle ZZ\rangle+\langle XX\rangle = 1+1 = 2 \quad\text{(ideal)}", size=40),
                Out("1.9267693296232773", id="o", hidden=True),
                T("los valores cambian en cada ejecución", "note", id="n", hidden=True),
                Box(
                    "idea",
                    "La brecha",
                    T("ideal 2 · con ruido ≈ 1,9 → supresión y mitigación (Parte VI)", "body"),
                    id="b",
                    hidden=True,
                ),
            ],
            [A("show", "o", at="sal"), A("show", "n", at="sal", t=1), A("show", "b", at="mens")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Clasifica esta tarea en uno de los cuatro pasos.""",
            [
                T(
                    "Reescribir una puerta Hadamard con rotaciones $R_z$ y $\\sqrt{X}$, y colocar las CZ solo entre qubits vecinos.",
                    "body",
                )
            ],
            ask=choice(
                "¿En qué paso del patrón ocurre?",
                ["Mapear", "Optimizar", "Ejecutar", "Posprocesar"],
                1,
                "Correcto: traducir a puertas base y respetar el mapa de acoplamiento es lo que produce un circuito ISA en el paso de optimización.",
                wrong=[
                    "Mapear produce circuitos abstractos; todavía no piensa en las puertas del hardware.",
                    None,
                    "Para ejecutar, el circuito ya debe ser ISA.",
                    "El posprocesamiento trabaja con resultados, no con circuitos.",
                ],
            ),
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Otra pregunta, sobre la ejecución.""",
            [
                T(
                    "Quieres la energía de una molécula: el valor esperado de su hamiltoniano.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué primitiva usarías?",
                ["Sampler", "Estimator"],
                1,
                "Correcto: Estimator devuelve valores esperados de observables, y además ofrece más opciones de mitigación.",
                wrong=[
                    "Con Sampler tendrías que reconstruir el valor esperado a partir de muestras; Estimator lo calcula directamente."
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. Abre el cuaderno de práctica de esta lección con el comando de abajo. [[n1]]Primero reproduces los cuatro pasos con el simulador exacto. [[n2]]Después cambias el observable y apuestas por el valor que saldrá.
             [[n3]]Y por último escribes el patrón como una función que sirve para cualquier circuito. [[check]]Cada misión tiene una comprobación que se actualiza sola: busca la marca verde.""",
            [
                Mission(
                    "practica/p1-patrones.py",
                    [
                        (1, "Ejecuta los cuatro pasos y comprueba que el circuito es ISA."),
                        (
                            2,
                            r"Añade `YY` al observable y predice $\langle ZZ\rangle+\langle XX\rangle+\langle YY\rangle$.",
                        ),
                        (
                            3,
                            "Escribe `patron(qc, obs, backend, nivel)` y pruébala con los niveles 0, 1 y 3.",
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
            """Antes de cerrar, dos preguntas para pensar. No hay respuesta automática: escribe con tus palabras. Lo que escribas se guarda y lo verás cuando vuelvas a esta lección.""",
            [T("Explicar con tus palabras es la mejor prueba de que entendiste.", "subtitle")],
            ask=reflect(
                "¿Por qué el paso de optimizar es obligatorio en un procesador real y no lo es en un simulador ideal? Explícalo con tus palabras.",
                "Elige un problema de tu área o de tu interés. ¿Cómo sería su paso uno, mapear? ¿Usarías Sampler o Estimator, y por qué?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Todo programa sigue cuatro pasos: mapear, optimizar, ejecutar y posprocesar. [[r2]]En hardware de IBM solo se ejecutan circuitos ISA: puertas base y conectividad del chip.
             [[r3]]Sampler da bits; Estimator, valores esperados. [[r4]]Las próximas partes del curso siguen este mismo orden.""",
            [
                L(
                    [
                        "mapear → optimizar → ejecutar → posprocesar",
                        "**ISA** = puertas base + mapa de acoplamiento",
                        "Sampler → bits · Estimator → $\\langle O\\rangle$",
                        "el curso sigue este orden: circuitos, transpilación, primitivas, ruido",
                    ],
                    id="r",
                    stagger=True,
                )
            ],
            [
                A("item", "r", at="r1", i=0),
                A("item", "r", at="r2", i=1),
                A("item", "r", at="r3", i=2),
                A("item", "r", at="r4", i=3),
            ],
        ),
    ],
    sources=["intro-to-patterns"],
    practice=[
        "Ejecuta el programa completo de la lección y cambia `optimization_level` a 0 y 3: compara `isa.count_ops()`.",
        'Cambia el observable a `SparsePauliOp(["ZZ", "XX", "YY"])`. ¿Qué valor ideal esperas para el estado de Bell?',
    ],
)

# ------------------------------------------------------------------ 1.3 Instalar
instalar = lesson(
    "p1-instalar",
    "Instalar y configurar Qiskit",
    "Entornos virtuales, pip, Jupyter, sistemas soportados, instalación desde el código fuente, configuración local y entornos en línea.",
    [
        "crear un entorno virtual e instalar Qiskit y el cliente de IBM",
        "resolver los errores de instalación más comunes",
        "configurar Qiskit con settings.conf y variables de entorno",
    ],
    [
        beat(
            "intro",
            ("", "Antes de instalar"),
            """Lo primero es Python. La página de Qiskit en el índice de paquetes, PyPI, indica qué versiones de Python soporta cada versión de Qiskit.
             [[venv]]Y lo recomendable es trabajar en un entorno virtual: un espacio aislado donde instalas lo que quieras sin tocar el Python base de tu máquina.
             [[ventaja]]Si algo se rompe, borras el entorno y empiezas de nuevo. [[donde]]Lo habitual es crearlo en una carpeta llamada punto venv dentro de cada proyecto.""",
            [
                T("Instalar Qiskit", "title"),
                Box(
                    "def",
                    "Entorno virtual",
                    T(
                        "un Python aislado para cada proyecto: si se corrompe, se borra y se rehace",
                        "body",
                    ),
                    id="b",
                    hidden=True,
                ),
                Code(
                    "mi-proyecto/\n├── .venv/        ← el entorno virtual\n└── programa.py",
                    "text",
                    id="t",
                    hidden=True,
                ),
            ],
            [A("show", "b", at="venv"), A("show", "t", at="donde")],
        ),
        beat(
            "venv",
            ("", "Crear y activar el entorno"),
            """Para crearlo, entra en la carpeta del proyecto y ejecuta python guion m venv punto venv. [[act]]Luego actívalo.
             [[unix]]En macOS y Linux, con source punto venv barra bin barra activate. [[win]]En Windows depende de la terminal: en PowerShell ejecutas el script Activate punto ps1; en Git Bash, source con la carpeta scripts; en la consola clásica, el archivo activate.""",
            [
                Sh("$ python -m venv .venv", id="a"),
                Row(
                    Box("def", "macOS · Linux", Sh("$ source .venv/bin/activate")),
                    Box(
                        "def",
                        "Windows",
                        Sh(
                            "PS> .venv\\Scripts\\Activate.ps1      # PowerShell\n$ source .venv/scripts/activate    # Git Bash\n> .venv\\Scripts\\activate          # cmd"
                        ),
                        id="w",
                        hidden=True,
                    ),
                    id="r",
                    hidden=True,
                    gap=24,
                ),
            ],
            [A("show", "r", at="act"), A("show", "w", at="win")],
        ),
        beat(
            "pip",
            ("", "Instalar con pip"),
            """Con el entorno activo, pip instala los paquetes. Con pip list ves lo que tienes.
             [[q]]Instala el SDK con pip install qiskit. [[vis]]Si vas a dibujar circuitos o usar cuadernos, añade el extra de visualización. [[jup]]Para Jupyter, instala jupyter y ábrelo con jupyter notebook.
             [[rt]]Si vas a usar los procesadores de IBM, instala también el cliente, qiskit ibm runtime. [[up]]Y revisa las notas de versión con frecuencia: pip install guion U actualiza.""",
            [
                Sh(
                    """$ pip install qiskit
$ pip install "qiskit[visualization]"
$ pip install jupyter && jupyter notebook
$ pip install qiskit-ibm-runtime
$ pip install -U qiskit qiskit-ibm-runtime""",
                    id="c",
                    reveal=True,
                )
            ],
            [
                A("lines", "c", at="q", to=1),
                A("lines", "c", at="vis", to=2),
                A("lines", "c", at="jup", to=3),
                A("lines", "c", at="rt", to=4),
                A("lines", "c", at="up", to=5),
            ],
        ),
        beat(
            "version",
            ("", "Comprobar la instalación"),
            """Para comprobar que todo quedó bien, importa qiskit e imprime su versión. [[out]]Este curso usa Qiskit dos punto cinco. [[sim]]Si solo vas a trabajar en local con los simuladores que trae Qiskit, ya terminaste. Para usar hardware de IBM falta crear tu cuenta, que veremos en la Parte cinco.""",
            [
                Code("import qiskit\nprint(qiskit.__version__)", id="c"),
                Out("2.5.2", id="o", hidden=True, check=True),
                Box(
                    "idea",
                    "Listo para simular",
                    T("para hardware de IBM: cuenta de IBM Cloud (Parte V)", "body"),
                    id="b",
                    hidden=True,
                ),
            ],
            [A("show", "o", at="out"), A("show", "b", at="sim")],
        ),
        beat(
            "so",
            ("", "Sistemas operativos"),
            """Qiskit clasifica los sistemas en tres niveles. [[t1]]Nivel uno: se prueban en cada cambio y tienen binarios precompilados. Linux x86 64, macOS con ARM, Windows de 64 bits y Linux AArch64.
             [[t2]]Nivel dos: binarios publicados pero sin pruebas durante el desarrollo, como macOS en Intel. [[t3]]Nivel tres: binarios sin probar; puede hacer falta un compilador, como Linux en ppc64le o s390x.
             [[64]]Desde Qiskit dos punto cero solo se soportan plataformas de 64 bits, [[cpy]]y solo el intérprete CPython; PyPy, por ejemplo, no.""",
            [
                Table(
                    ["Nivel", "Qué significa", "Sistemas"],
                    [
                        [
                            "1",
                            "probado en cada cambio · binarios",
                            "Linux x86_64, macOS ARM64, Windows 64 bits, Linux AArch64",
                        ],
                        ["2", "binarios, sin pruebas en desarrollo", "macOS x86_64"],
                        [
                            "3",
                            "binarios sin probar · quizá compilador",
                            "Linux ppc64le, Linux s390x",
                        ],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                ),
                T(
                    "solo 64 bits (desde 2.0) · solo CPython",
                    "note",
                    id="n",
                    hidden=True,
                    color="red",
                ),
            ],
            [
                A("item", "t", at="t1", i=0),
                A("item", "t", at="t2", i=1),
                A("item", "t", at="t3", i=2),
                A("show", "n", at="64"),
            ],
        ),
        beat(
            "errores",
            ("", "Problemas frecuentes"),
            """Dos problemas aparecen a menudo. [[nomod]]El primero: no module named qiskit en un cuaderno, aunque lo instalaste. Casi siempre Jupyter está corriendo en otro entorno, por ejemplo el entorno base de Anaconda. La solución es abrir Jupyter desde el entorno donde instalaste Qiskit.
             [[wheel]]El segundo: failed building wheel. Algún paquete no tiene binarios para tu plataforma y pip intenta compilarlo; revisa la documentación de ese paquete para instalar lo que necesita para compilar.""",
            [
                Box(
                    "warn",
                    "No module named 'qiskit'",
                    T("Jupyter corre en otro entorno → ábrelo desde el entorno con Qiskit", "body"),
                    id="a",
                    hidden=True,
                ),
                Box(
                    "warn",
                    "Failed building wheel for …",
                    T("faltan binarios → instala lo necesario para compilar ese paquete", "body"),
                    id="b",
                    hidden=True,
                ),
            ],
            [A("show", "a", at="nomod"), A("show", "b", at="wheel")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Un caso práctico.""",
            [
                T(
                    "Instalaste Qiskit en tu entorno `.venv`, pero abriste Jupyter desde Anaconda Navigator y `import qiskit` falla.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué es lo más probable?",
                [
                    "Qiskit no soporta Jupyter",
                    "Jupyter está usando otro entorno, sin Qiskit",
                    "Falta compilar Qiskit con Rust",
                    "Tu sistema es de nivel 3",
                ],
                1,
                "Correcto: el cuaderno corre en un entorno donde Qiskit no está instalado. Elige el entorno correcto o lanza Jupyter desde él.",
                wrong=[
                    "Qiskit funciona en Jupyter sin problema.",
                    None,
                    "Solo se compila con Rust si instalas desde el código fuente.",
                    "Ese error se debe al entorno, no al sistema operativo.",
                ],
            ),
        ),
        beat(
            "fuente",
            ("", "Instalar desde el código fuente"),
            """Si quieres la versión en desarrollo, o contribuir, puedes instalar desde el código fuente. [[rust]]Parte del SDK está escrito en Rust, así que necesitas un compilador de Rust; lo más fácil es rustup.
             [[clone]]Clonas el repositorio, entras a la carpeta, [[dev]]instalas los requisitos de desarrollo si vas a correr pruebas, [[edit]]e instalas en modo editable, con pip install guion e punto.
             [[rel]]En modo editable, las extensiones se compilan sin optimizar. Para compilarlas en modo release usa build rust con guion guion release. Y si cambias código en Rust, debes volver a compilar.
             [[rt]]El cliente de IBM se instala igual desde su propio repositorio, sin Rust.""",
            [
                Sh(
                    """$ git clone https://github.com/Qiskit/qiskit.git
$ cd qiskit
$ pip install -r requirements-dev.txt     # opcional: pruebas
$ pip install -e .                        # modo editable
$ python setup.py build_rust --release --inplace""",
                    id="c",
                    reveal=True,
                ),
                Box(
                    "def",
                    "Requisito",
                    T("compilador de Rust (rustup)", "body"),
                    id="r",
                    hidden=True,
                ),
                T(
                    'cliente: `git clone …/qiskit-ibm-runtime.git` · `pip install -e ".[dev]"`',
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("show", "r", at="rust"),
                A("lines", "c", at="clone", to=2),
                A("lines", "c", at="dev", to=3),
                A("lines", "c", at="edit", to=4),
                A("lines", "c", at="rel", to=5),
                A("show", "n", at="rt"),
            ],
        ),
        beat(
            "predice_config",
            ("", "Antes de configurar"),
            """Antes de ver la configuración, apuesta. Imagina que tu archivo settings punto conf fija el nivel de optimización por defecto en cero.
             [[cual]]Luego transpilas, sin indicar ningún nivel, un circuito con dos Hadamard seguidas. Dos Hadamard seguidas se cancelan entre sí. ¿Cuántas quedan?""",
            [
                Code(
                    """# settings.conf: transpile_optimization_level = 0
qc = QuantumCircuit(1)
qc.h(0)
qc.h(0)
print(dict(transpile(qc).count_ops()))""",
                    id="c",
                    norun=True,
                    size=26,
                )
            ],
            [A("hl", "c", at="cual", lines=[2, 3, 5])],
            ask=predict(
                "¿Cuántas Hadamard quedan en el circuito transpilado?",
                [
                    "ninguna: el transpilador las cancela",
                    "una",
                    "las dos",
                    "no se puede saber sin indicar el nivel",
                ],
                "Anotado. Veamos qué dice la configuración.",
            ),
        ),
        beat(
            "config",
            ("", "Configuración local"),
            """Qiskit lee un archivo de configuración opcional, settings punto conf, en la carpeta punto qiskit de tu usuario. [[env]]Otra ruta se indica con la variable QISKIT SETTINGS.
             [[draw]]Con circuit drawer eliges el dibujante por defecto: texto, matplotlib o LaTeX. [[style]]Con circuit mpl style, el estilo de matplotlib. [[state]]Con state drawer, cómo se dibujan los estados.
             [[opt]]transpile optimization level fija el nivel de optimización por defecto de la función transpile, de cero a tres; generate preset pass manager tiene su propio nivel por defecto. [[cero]]Con cero no se optimiza nada: las dos Hadamard se quedan, aunque se cancelen. Si apostaste por las dos, acertaste. [[par]]parallel y num processes controlan el paralelismo con varios procesos.
             [[qpy]]Y min qpy version rechaza archivos QPY antiguos, por seguridad.""",
            [
                Code(
                    """[default]
circuit_drawer = mpl
circuit_mpl_style = default
state_drawer = hinton
transpile_optimization_level = 3
parallel = False
num_processes = 15
min_qpy_version = 14""",
                    "text",
                    title="~/.qiskit/settings.conf",
                    id="c",
                ),
                T("otra ruta: variable `QISKIT_SETTINGS`", "note", id="n", hidden=True),
                T(
                    "con nivel 0, dos `h` seguidas siguen siendo `{'h': 2}`",
                    "note",
                    id="z",
                    hidden=True,
                ),
            ],
            [
                A("show", "n", at="env"),
                A("hl", "c", at="draw", lines=[2]),
                A("hl", "c", at="style", lines=[3]),
                A("hl", "c", at="state", lines=[4]),
                A("hl", "c", at="opt", lines=[5]),
                A("show", "z", at="cero"),
                A("hl", "c", at="par", lines=[6, 7]),
                A("hl", "c", at="qpy", lines=[8]),
            ],
        ),
        beat(
            "variables",
            ("", "Variables de entorno"),
            """Algunas variables de entorno cambian el comportamiento de Qiskit. [[par]]QISKIT PARALLEL activa el multiprocesamiento, y QISKIT NUM PROCS limita cuántos procesos lanza.
             [[ray]]RAYON NUM THREADS fija el número de hilos del código multihilo, que por defecto usa uno por cada CPU lógica.
             [[force]]Si Qiskit ya está en paralelo con procesos, no lanza además hilos, para no saturar la CPU; QISKIT FORCE THREADS lo obliga.
             [[sabre]]Y QISKIT SABRE ALL THREADS hace que el algoritmo de layout y routing use todas las CPU para sus intentos aleatorios: mejora los resultados con muchos núcleos, pero ya no son reproducibles en otra máquina.""",
            [
                Table(
                    ["Variable", "Efecto"],
                    [
                        [
                            "`QISKIT_PARALLEL` · `QISKIT_NUM_PROCS`",
                            "multiprocesamiento y número máximo de procesos",
                        ],
                        [
                            "`RAYON_NUM_THREADS`",
                            "hilos del código multihilo (por defecto, uno por CPU lógica)",
                        ],
                        ["`QISKIT_FORCE_THREADS`", "usar hilos aun dentro de procesos paralelos"],
                        [
                            "`QISKIT_SABRE_ALL_THREADS`",
                            "SABRE usa todas las CPU · mejor calidad, menos reproducible",
                        ],
                    ],
                    id="t",
                    stagger=True,
                    size=23,
                )
            ],
            [
                A("item", "t", at="par", i=0),
                A("item", "t", at="ray", i=1),
                A("item", "t", at="force", i=2),
                A("item", "t", at="sabre", i=3),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Una pregunta sobre configuración.""",
            [T("Quieres que Qiskit use como máximo 4 hilos en sus funciones multihilo.", "body")],
            ask=choice(
                "¿Qué variable defines?",
                [
                    "`QISKIT_NUM_PROCS=4`",
                    "`RAYON_NUM_THREADS=4`",
                    "`QISKIT_PARALLEL=4`",
                    "`transpile_optimization_level = 4`",
                ],
                1,
                "Correcto: `RAYON_NUM_THREADS` controla los hilos; `QISKIT_NUM_PROCS` controla procesos, que son otra cosa.",
                wrong=[
                    "Esa variable limita procesos, no hilos.",
                    None,
                    "`QISKIT_PARALLEL` es verdadero o falso.",
                    "Ese es el nivel de optimización, que va de 0 a 3.",
                ],
            ),
        ),
        beat(
            "online",
            ("", "Sin instalar nada"),
            """También puedes trabajar en línea. [[pre]]Hay entornos con Qiskit ya instalado: los cuadernos de inteligencia artificial de OVHcloud, que no están disponibles en todas las regiones, y qBraid Lab, donde añades el entorno de Qiskit desde su panel.
             [[otros]]Y en Google Colab, Watson Studio o Azure Machine Learning Studio basta con instalarlo en una celda, con por ciento pip install qiskit.""",
            [
                Row(
                    Box(
                        "def",
                        "Con Qiskit preinstalado",
                        L(["OVHcloud AI Notebooks", "qBraid Lab"], size=27),
                    ),
                    Box(
                        "idea",
                        "Instalándolo tú",
                        L(["Google Colab", "IBM Watson Studio", "Azure ML Studio"], size=27),
                        id="b",
                        hidden=True,
                    ),
                    id="r",
                    hidden=True,
                    gap=26,
                ),
                Code("%pip install qiskit", id="c", hidden=True, norun=True),
            ],
            [A("show", "r", at="pre"), A("show", "b", at="otros"), A("show", "c", at="otros", t=1)],
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. Abre el cuaderno de práctica de esta lección con el comando de abajo. [[n1]]Primero compruebas tu instalación: la versión de Qiskit y el intérprete de Python. [[n2]]Después editas un archivo settings punto conf y compruebas que Qiskit lo lee.
             [[n3]]Y por último escribes dos funciones que convierten cuadernos entre Jupyter y marimo, con marimo convert. Así podrás usar las guías de IBM, que están en Jupyter. [[check]]Cada misión tiene una comprobación que se actualiza sola: busca la marca verde.""",
            [
                Mission(
                    "practica/p1-instalar.py",
                    [
                        (
                            1,
                            "Comprueba tu versión de Qiskit y que tu Python es CPython de 64 bits.",
                        ),
                        (2, "Edita un `settings.conf`: dibujo `mpl` y `transpile` sin optimizar."),
                        (
                            3,
                            "Escribe `jupyter_a_marimo` y `marimo_a_jupyter` con `marimo convert` y `marimo export ipynb`.",
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
            """Antes de cerrar, dos preguntas para pensar. No hay respuesta automática: escribe con tus palabras. Lo que escribas se guarda y lo verás cuando vuelvas a esta lección.""",
            [T("Explicar con tus palabras es la mejor prueba de que entendiste.", "subtitle")],
            ask=reflect(
                "¿Qué ventaja te da un entorno virtual por proyecto? Cuéntalo con un ejemplo de algo que podría salir mal sin él.",
                "Un cuaderno de marimo es un archivo `.py`; uno de Jupyter es un `.ipynb`. ¿Qué ventaja ves en el primero, y cuándo necesitarías convertirlo a Jupyter?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Trabaja en un entorno virtual por proyecto. [[r2]]pip install qiskit para el SDK, y qiskit ibm runtime para el hardware de IBM. [[r3]]Si un cuaderno no encuentra Qiskit, revisa el entorno.
             [[r4]]Y settings punto conf, junto con unas pocas variables de entorno, ajustan dibujos, optimización y paralelismo.""",
            [
                L(
                    [
                        "un entorno virtual por proyecto (`.venv`)",
                        "`pip install qiskit` · `pip install qiskit-ibm-runtime`",
                        "«No module named qiskit» → otro entorno",
                        "`~/.qiskit/settings.conf` y `RAYON_NUM_THREADS`, `QISKIT_PARALLEL`…",
                    ],
                    id="r",
                    stagger=True,
                )
            ],
            [
                A("item", "r", at="r1", i=0),
                A("item", "r", at="r2", i=1),
                A("item", "r", at="r3", i=2),
                A("item", "r", at="r4", i=3),
            ],
        ),
    ],
    sources=[
        "install-qiskit",
        "install-qiskit-source",
        "configure-qiskit-local",
        "online-lab-environments",
        "install-qiskit-runtime",
        "install-qiskit-runtime-source",
    ],
    practice=[
        "Crea un proyecto nuevo con su `.venv`, instala `qiskit[visualization]` y `qiskit-ibm-runtime`, y comprueba las versiones.",
        "Crea `~/.qiskit/settings.conf` con `circuit_drawer = mpl` y verifica que `qc.draw()` ya dibuja con matplotlib.",
    ],
)

# ------------------------------------------------------------------ 1.4 Quickstart
BELL = """
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

sampler = StatevectorSampler()
result = sampler.run([qc], shots=1024).result()
print(result[0].data.meas.get_counts())
"""
quickstart = lesson(
    "p1-quickstart",
    "Tu primer circuito: el estado de Bell",
    "Construir, simular y graficar un estado entrelazado en pocas líneas, sin cuenta ni clave.",
    [
        "construir un circuito con `QuantumCircuit`, `h`, `cx` y `measure_all`",
        "ejecutarlo con `StatevectorSampler` y leer los conteos",
        "interpretar el resultado como una firma del entrelazamiento",
    ],
    [
        beat(
            "intro",
            ("", "En menos de dos minutos"),
            """Vamos a construir tu primer circuito cuántico, en tu computadora, sin cuenta ni clave de acceso. [[que]]Será un estado de Bell: dos qubits entrelazados.
             [[req]]Solo necesitas qiskit, matplotlib y el extra de visualización.""",
            [
                T("Tu primer circuito", "title"),
                T("un estado de Bell: dos qubits entrelazados", "subtitle", id="s", hidden=True),
                Sh('$ pip install qiskit matplotlib "qiskit[visualization]"', id="c", hidden=True),
            ],
            [A("show", "s", at="que"), A("show", "c", at="req")],
        ),
        beat(
            "construir",
            ("", "Construir el circuito"),
            """Importamos QuantumCircuit [[nuevo]]y creamos un circuito con dos qubits. Ambos empiezan en el estado cero.
             [[h]]Aplicamos una Hadamard al qubit cero, [[cx]]luego una CNOT con el qubit cero como control y el uno como objetivo, [[m]]y medimos todos los qubits con measure all, que además añade una barrera y un registro clásico llamado meas.""",
            [
                Row(
                    Code(BELL, id="c", reveal=True, size=22, maxw=620),
                    Circ(
                        2,
                        [
                            G("h", 0, hidden=True),
                            G("cx", 0, 1, hidden=True),
                            G("barrier", hidden=True),
                            G("measure", 0, c=0, hidden=True),
                            G("measure", 1, c=1, hidden=True),
                        ],
                        clbits=2,
                        creg="meas",
                        id="q",
                        hidden=True,
                        maxw=480,
                    ),
                    gap=30,
                )
            ],
            [
                A("lines", "c", at="nuevo", to=4),
                A("show", "q", at="nuevo"),
                A("lines", "c", at="h", to=5),
                A("gate", "q", at="h", i=0),
                A("lines", "c", at="cx", to=6),
                A("gate", "q", at="cx", i=1),
                A("lines", "c", at="m", to=7),
                A("gate", "q", at="m", i=[2, 3, 4]),
            ],
        ),
        beat(
            "predice",
            ("", "Antes de ejecutar"),
            """Antes de ejecutarlo, apuesta. Mediremos los dos qubits mil veinticuatro veces. [[cual]]¿Qué cadenas de bits crees que aparecerán? No hace falta que sepas la respuesta: equivocarse en una predicción enseña más que acertar por memoria.""",
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
                )
            ],
            ask=predict(
                "Tras 1024 disparos, ¿qué esperas ver?",
                [
                    "las cuatro cadenas (`00`, `01`, `10`, `11`), cerca de 256 cada una",
                    "solo `00` y `11`, cerca de 512 cada una",
                    "siempre `00`",
                    "solo `01` y `10`",
                ],
                "Anotado. Ahora ejecutémoslo y veamos si acertaste.",
            ),
        ),
        beat(
            "ejecutar",
            ("", "Ejecutar con un Sampler"),
            """Para ejecutarlo usamos una primitiva. StatevectorSampler simula el circuito de forma exacta y luego toma muestras, como si fuera un computador cuántico ideal.
             [[run]]run recibe una lista de circuitos, aquí uno solo, y el número de disparos: mil veinticuatro. result espera a que termine.
             [[leer]]Leer el resultado es una cadena: el primer elemento de la lista, punto data, [[meas]]punto meas, que es el registro creado por measure all, [[counts]]y get counts, que cuenta cuántas veces salió cada cadena de bits.""",
            [
                Code(BELL, id="c", size=24),
                Flow(
                    [
                        dict(t="result[0]", s="un circuito"),
                        dict(t=".data", s="sus datos"),
                        dict(t=".meas", s="el registro"),
                        dict(t=".get_counts()", s="conteos"),
                    ],
                    id="f",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="run", lines=[9, 10]),
                A("hl", "c", at="leer", lines=[11]),
                A("show", "f", at="leer"),
                A("step", "f", at="leer", i=[0, 1]),
                A("step", "f", at="meas", i=2),
                A("step", "f", at="counts", i=3),
            ],
        ),
        beat(
            "resultado",
            ("", "El resultado"),
            """Esto es lo que imprime. [[mitad]]Casi la mitad de las veces sale cero cero, y la otra mitad, uno uno. [[nunca]]Nunca sale cero uno ni uno cero. Si apostaste por la opción b, acertaste; si no, mejor todavía: ahora vale la pena entender por qué.
             [[azar]]Los números exactos cambian en cada ejecución, porque son muestras aleatorias.""",
            [
                Out("{'11': 510, '00': 514}", id="o"),
                Hist(
                    [["00", 514], ["01", 0], ["10", 0], ["11", 510]],
                    id="h",
                    grow=True,
                    ymax=600,
                    color="blue",
                ),
                T("cada ejecución da números un poco distintos", "note", id="n", hidden=True),
            ],
            [A("grow", "h", at="mitad", dur=1.4), A("show", "n", at="azar")],
        ),
        beat(
            "estado",
            ("", "Qué estado se prepara"),
            """¿Por qué solo cero cero y uno uno? Sigamos el estado paso a paso. [[ini]]Al principio, cero cero. [[h]]La Hadamard pone al qubit cero en superposición: cero más uno, sobre raíz de dos.
             [[cx]]La CNOT invierte el qubit uno solo cuando el qubit cero vale uno. El término con el cero se queda igual y el término con el uno se convierte en uno uno.
             [[bell]]El resultado es el estado de Bell: cero cero más uno uno, sobre raíz de dos. Ninguno de los dos qubits tiene un valor propio; solo están perfectamente correlacionados.
             [[orden]]Un detalle de notación: Qiskit escribe el qubit cero a la derecha. Lo verás en una lección propia.""",
            [
                Circ(2, [G("h", 0), G("cx", 0, 1)], id="q"),
                M(r"|00\rangle", id="a", size=40),
                M(
                    r"\xrightarrow{H_0}\ \tfrac{1}{\sqrt2}\big(|00\rangle+|0\gold{1}\rangle\big)",
                    id="b",
                    hidden=True,
                    size=40,
                ),
                M(
                    r"\xrightarrow{CX}\ \tfrac{1}{\sqrt2}\big(|00\rangle+|\gold{11}\rangle\big)",
                    id="c",
                    hidden=True,
                    size=40,
                    color="fg",
                ),
                T(
                    "en $|q_1q_0\\rangle$ el qubit 0 va a la **derecha**",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("cursor", "q", at="h", col=0),
                A("show", "b", at="h"),
                A("cursor", "q", at="cx", col=1),
                A("show", "c", at="cx"),
                A("emph", "c", at="bell"),
                A("show", "n", at="orden"),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Piensa en el estado de Bell.""",
            [M(r"\tfrac{1}{\sqrt2}\big(|00\rangle+|11\rangle\big)", size=46)],
            ask=numeric(
                "Si mides solo el qubit 0, ¿con qué probabilidad sale 1?",
                0.5,
                "Correcto: 1/2. Cada qubit por separado es completamente aleatorio; lo que no es aleatorio es la relación entre los dos.",
                tol=0.001,
                hint="Suma las probabilidades de los resultados en los que el qubit 0 vale 1.",
                solution=[
                    "El qubit 0 vale 1 solo en $|11\\rangle$, con probabilidad $|1/\\sqrt2|^2=1/2$."
                ],
            ),
        ),
        beat(
            "entrelazamiento",
            ("", "La firma del entrelazamiento"),
            """Este resultado es una firma del entrelazamiento. [[cada]]Cada qubit por separado es una moneda perfecta: cero o uno, mitad y mitad.
             [[juntos]]Pero los dos siempre coinciden. Si sabes lo que salió en uno, sabes lo que saldrá en el otro.
             [[clas]]Una correlación así podría imitarse con monedas trucadas. Lo que no se puede imitar clásicamente aparece cuando se mide en otras bases, y lo verás con Estimator.""",
            [
                Row(
                    Box(
                        "def",
                        "Cada qubit",
                        T("0 o 1 al azar, 50 % · 50 %", "body"),
                        id="a",
                        hidden=True,
                    ),
                    Box(
                        "idea",
                        "Los dos juntos",
                        T("siempre iguales: 00 o 11", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=26,
                ),
                T(
                    "medir en otras bases (por ejemplo $\\langle XX\\rangle$) revela lo que ninguna moneda clásica imita",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [A("show", "a", at="cada"), A("show", "b", at="juntos"), A("show", "n", at="clas")],
        ),
        beat(
            "histograma",
            ("", "Graficar"),
            """Para ver un histograma, importa plot histogram de qiskit punto visualization y pásale los conteos. [[plt]]En un cuaderno aparece solo; en un programa normal, necesitas además matplotlib punto pyplot y plt punto show.""",
            [
                Code(
                    """from qiskit.visualization import plot_histogram

counts = result[0].data.meas.get_counts()
plot_histogram(counts)
# fuera de Jupyter:
# import matplotlib.pyplot as plt
# plt.show()""",
                    id="c",
                )
            ],
            [A("hl", "c", at="plt", range="5-7")],
        ),
        beat(
            "ghz_pred",
            ("", "Tres qubits"),
            """Un paso más. Con tres qubits, añadimos una segunda CNOT, del qubit uno al dos.""",
            [Circ(3, [G("h", 0), G("cx", 0, 1), G("cx", 1, 2)])],
            ask=predict(
                "¿Qué cadenas aparecerán ahora?",
                [
                    "solo `000` y `111`",
                    "`000`, `011` y `111`",
                    "las ocho cadenas por igual",
                    "solo `001` y `110`",
                ],
                "Anotado. Veamos.",
            ),
        ),
        beat(
            "ghz",
            ("", "Experimenta: tres qubits"),
            """Este es el código. [[cx]]La única diferencia es la segunda CNOT.
             [[res]]Las mediciones dan solo cero cero cero y uno uno uno: la CNOT copia la correlación al tercer qubit, y los tres quedan entrelazados. Es un estado GHZ.""",
            [
                Code(
                    """qc = QuantumCircuit(3)
qc.h(0)
qc.cx(0, 1)
qc.cx(1, 2)
qc.measure_all()
print(StatevectorSampler().run([qc]).result()[0].data.meas.get_counts())""",
                    id="c",
                ),
                Circ(3, [G("h", 0), G("cx", 0, 1), G("cx", 1, 2, hidden=True)], id="q"),
                Out("{'111': 513, '000': 511}", id="o", hidden=True),
            ],
            [
                A("gate", "q", at="cx", i=2),
                A("hl", "c", at="cx", lines=[4]),
                A("show", "o", at="res"),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Piensa en el circuito de tres qubits que acabamos de medir.""",
            [
                Circ(
                    3,
                    [
                        G("h", 0),
                        G("cx", 0, 1),
                        G("cx", 1, 2),
                        G("barrier"),
                        G("measure", 0, c=0),
                        G("measure", 1, c=1),
                        G("measure", 2, c=2),
                    ],
                    clbits=3,
                    creg="meas",
                )
            ],
            ask=choice(
                "Mides los tres qubits y el qubit 2 da `1`. ¿Qué dan el qubit 0 y el qubit 1?",
                [
                    "`0` y `0`",
                    "`1` y `1`",
                    "cada uno al azar",
                    "el qubit 1 da `1` y el qubit 0 queda al azar",
                ],
                1,
                "Correcto: las dos CNOT copian el valor del qubit 0 al 1 y de ahí al 2, así que los tres coinciden siempre. Si el 2 vale 1, los otros dos también.",
                wrong=[
                    "Saldría una cadena con un solo `1`, y esa nunca aparece.",
                    None,
                    "Los tres qubits están correlacionados: no son monedas independientes.",
                    "La primera CNOT hace que el qubit 1 copie al qubit 0: los dos coinciden siempre.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. [[n1]]Primero reproduces el estado de Bell. [[n2]]Después lo modificas para que los qubits salgan siempre distintos. [[n3]]Y por último creas una función que prepara un estado GHZ de cualquier tamaño.
             [[check]]Escribe tu código en el editor y pulsa Comprobar: los casos se corren en esta misma página.""",
            [
                Mission(
                    "practica/p1-quickstart.py",
                    [(1, "Ejecuta el estado de Bell y lee sus conteos.")],
                    id="m",
                    stagger=True,
                ),
                Exercise(
                    "p1-quickstart/bell-distinto",
                    r"Prepara $\tfrac{1}{\sqrt2}(|01\rangle+|10\rangle)$ añadiendo una sola puerta al circuito.",
                    level=2,
                    id="e2",
                    hidden=True,
                    hints=[
                        "Hoy los dos qubits salen iguales. Necesitas una puerta que invierta uno de ellos, de 0 a 1 y de 1 a 0: el NOT cuántico, la puerta `X`.",
                        "Va después de la CNOT y antes de `measure_all()`, donde está el comentario.",
                        "Es una puerta de un solo qubit: lleva un único argumento, el qubit que invierte.",
                    ],
                ),
                Exercise(
                    "p1-quickstart/ghz",
                    "Escribe `ghz(n)`: `n` es el número de qubits (2 o más). Devuelve un `QuantumCircuit` de `n` qubits, medido con `measure_all()`, que solo da `00…0` o `11…1`. Ojo: el GHZ de la lección tiene 3 qubits escritos a mano; el tuyo debe valer para cualquier `n`.",
                    level=3,
                    id="e3",
                    hidden=True,
                    hints=[
                        "Un GHZ pone un qubit en superposición y propaga esa correlación al resto, de uno en uno.",
                        "Después de la superposición, un bucle recorre los pares de qubits vecinos: una cadena de `n` qubits tiene `n - 1` pares.",
                        "En cada vuelta va una sola puerta de dos qubits, y sus dos argumentos se calculan con el contador del bucle.",
                    ],
                ),
            ],
            [A("item", "m", at="n1", i=0), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "proyecto",
            ("", "Tu proyecto: una cadena de espines"),
            """Además de las misiones de cada lección, a lo largo del curso vas a construir un solo proyecto: simular una cadena de espines, el modelo de Ising con campo transversal, y terminar ejecutándolo en un computador cuántico real.
             [[terminos]]El término Z Z quiere alinear a los vecinos; el término X los hace girar. La pregunta que vas a responder: cómo evoluciona la magnetización cuando se enciende el campo de golpe.
             [[hito]]Hoy empieza el hito uno: crea tu cuenta gratuita de IBM Quantum, y construye un paso de tiempo para dos espines. Comprobarás qué tan buena es la aproximación.""",
            [
                M(r"H = J\sum_i Z_iZ_{i+1} + h\sum_i X_i", size=46),
                Row(
                    Box(
                        "def", r"$J\,ZZ$", T("alinea espines vecinos", "body"), id="a", hidden=True
                    ),
                    Box("idea", r"$h\,X$", T("los hace girar", "body"), id="b", hidden=True),
                    gap=24,
                ),
                Mission(
                    "practica/proyecto/hito1.py",
                    [
                        (
                            1,
                            "Crea tu cuenta de IBM Quantum (plan Open) y escribe el Hamiltoniano de 2 espines.",
                        ),
                        (2, "Construye un paso de Trotter con `rzz` y `rx`."),
                        (
                            3,
                            "Calcula la fidelidad frente a la evolución exacta y mira cómo cae al agrandar $dt$.",
                        ),
                    ],
                    title="Proyecto Ising · Hito I",
                    id="m",
                    hidden=True,
                ),
            ],
            [
                A("show", "a", at="terminos"),
                A("show", "b", at="terminos", t=2),
                A("show", "m", at="hito"),
            ],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Antes de cerrar, dos preguntas para pensar. No hay respuesta automática: escribe con tus palabras. Lo que escribas se guarda y lo verás cuando vuelvas a esta lección.""",
            [T("Explicar con tus palabras es la mejor prueba de que entendiste.", "subtitle")],
            ask=reflect(
                "¿Por qué en el estado de Bell **nunca** sale `01`? Explícalo sin fórmulas, como a un compañero.",
                "Dos monedas trucadas que siempre caen igual también darían solo `00` y `11`. ¿Qué crees que haría falta medir para distinguirlas de un estado entrelazado?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]QuantumCircuit con h, cx y measure all construye un estado de Bell. [[r2]]StatevectorSampler lo ejecuta localmente, sin cuenta. [[r3]]Los conteos se leen con result, data, el nombre del registro y get counts.
             [[r4]]Y la correlación perfecta, cero cero o uno uno, es la firma del entrelazamiento. En la próxima lección, una herramienta gráfica para hacer lo mismo sin código: Composer.""",
            [
                L(
                    [
                        "`QuantumCircuit(2)` · `h(0)` · `cx(0, 1)` · `measure_all()`",
                        "`StatevectorSampler().run([qc], shots=1024)`",
                        "`result[0].data.meas.get_counts()`",
                        "solo `00` y `11`: entrelazamiento",
                    ],
                    id="r",
                    stagger=True,
                )
            ],
            [
                A("item", "r", at="r1", i=0),
                A("item", "r", at="r2", i=1),
                A("item", "r", at="r3", i=2),
                A("item", "r", at="r4", i=3),
            ],
        ),
    ],
    sources=["quick-start"],
    practice=[
        "Prepara el estado $(|01\\rangle+|10\\rangle)/\\sqrt2$ con una X adicional y comprueba los conteos.",
        "Generaliza a $n$ qubits con un bucle `for` y mide hasta $n=10$. ¿Cambia el tiempo de simulación?",
    ],
)

# ------------------------------------------------------------------ 1.5 Composer
composer = lesson(
    "p1-composer",
    "IBM Quantum Composer",
    "La herramienta gráfica de IBM: construir con arrastrar y soltar o con OpenQASM, inspeccionar paso a paso, ejecutar en QPUs y leer sus visualizaciones.",
    [
        "recorrer las partes de la interfaz de Composer",
        "construir circuitos con arrastrar y soltar o con OpenQASM 2.0",
        "interpretar el disco de fase, la q-esfera y las vistas de probabilidades y vector de estado",
    ],
    [
        beat(
            "intro",
            ("", "Programar arrastrando puertas"),
            """IBM Quantum Composer es una herramienta gráfica: arrastras puertas sobre los cables de los qubits y construyes circuitos sin escribir código.
             [[vis]]Mientras construyes, ves cómo cambia el estado de los qubits. [[run]]Puedes ejecutar el circuito en hardware cuántico real. [[code]]Y genera automáticamente el código OpenQASM o Qiskit equivalente.""",
            [
                T("IBM Quantum Composer", "title"),
                Row(
                    Box("def", "Visualizar", T("estados en vivo", "body"), id="a", hidden=True),
                    Box("def", "Ejecutar", T("en QPUs reales", "body"), id="b", hidden=True),
                    Box(
                        "def", "Generar código", T("OpenQASM y Qiskit", "body"), id="c", hidden=True
                    ),
                    gap=22,
                ),
            ],
            shows(("vis", "a"), ("run", "b"), ("code", "c")),
        ),
        beat(
            "interfaz",
            ("", "La interfaz"),
            """La interfaz tiene seis partes. [[cat]]El catálogo de operaciones: las piezas, agrupadas por color; con clic derecho e Info ves la definición de cada una.
             [[ed]]El editor de código: el OpenQASM se puede editar, el de Qiskit es de solo lectura. [[gr]]El editor gráfico, donde arrastras las puertas a los cables.
             [[bar]]La barra de herramientas, con deshacer, alineación y el modo inspección. [[disk]]Los discos de fase al final de cada cable. [[viz]]Y las visualizaciones, que vienen de un simulador de vector de estado e ignoran las mediciones.""",
            [
                Table(
                    ["Parte", "Para qué"],
                    [
                        [
                            "Catálogo de operaciones",
                            "las puertas, por colores · clic derecho → Info",
                        ],
                        ["Editor de código", "OpenQASM (editable) · Qiskit (solo lectura)"],
                        ["Editor gráfico", "arrastrar puertas a los cables"],
                        ["Barra de herramientas", "deshacer · alineación · modo **inspección**"],
                        ["Discos de fase", "estado local de cada qubit al final"],
                        ["Visualizaciones", "simulador de vector de estado · ignora mediciones"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                )
            ],
            [
                A("item", "t", at="cat", i=0),
                A("item", "t", at="ed", i=1),
                A("item", "t", at="gr", i=2),
                A("item", "t", at="bar", i=3),
                A("item", "t", at="disk", i=4),
                A("item", "t", at="viz", i=5),
            ],
        ),
        beat(
            "construir",
            ("", "Construir y editar"),
            """Sin iniciar sesión, las visualizaciones funcionan con hasta cuatro qubits; para más, o para ejecutar en hardware, debes iniciar sesión.
             [[alin]]Hay tres alineaciones: libre, a la izquierda, y por capas, que marca el orden de ejecución con columnas. [[grupo]]Puedes seleccionar varias operaciones y agruparlas en una operación propia, que aparece como una sola caja; o desagruparla, o expandir su definición sin desagrupar.
             [[reg]]Desde el menú Edit gestionas los registros. [[if]]Arrastrando la operación if sobre una puerta le pones una condición clásica, [[ctrl]]y el modificador de control la convierte en una puerta controlada.
             [[save]]Importante: para conservar tu trabajo, descarga el archivo punto qasm y vuelve a subirlo después.""",
            [
                L(
                    [
                        "alineación: libre · izquierda · **por capas**",
                        "agrupar → operación propia · desagrupar · expandir definición",
                        "Edit → Manage registers",
                        "`if` sobre una puerta: condición clásica",
                        "modificador de control → puerta controlada",
                    ],
                    id="l",
                    stagger=True,
                    size=28,
                ),
                Box(
                    "warn",
                    "Guarda tu circuito",
                    T("File → Save file (.qasm) · después: Upload .qasm file", "body"),
                    id="b",
                    hidden=True,
                ),
            ],
            [
                A("item", "l", at="alin", i=0),
                A("item", "l", at="grupo", i=1),
                A("item", "l", at="reg", i=2),
                A("item", "l", at="if", i=3),
                A("item", "l", at="ctrl", i=4),
                A("show", "b", at="save"),
            ],
        ),
        beat(
            "qasm",
            ("", "Construir con OpenQASM"),
            """También puedes escribir el circuito en el editor de código, en OpenQASM dos punto cero. [[cab]]El archivo empieza con la versión e incluye la biblioteca estándar de puertas.
             [[reg]]Declaras registros cuánticos y clásicos, [[ops]]aplicas puertas y mides con una flecha hacia el bit clásico.
             [[gate]]Y puedes definir tus propias puertas con la palabra gate: un nombre, parámetros opcionales y los qubits sobre los que actúa. Luego se usa como cualquier otra.""",
            [
                Code(
                    """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
gate bell a, b { h a; cx a, b; }
bell q[0], q[1];
measure q -> c;""",
                    "qasm",
                    id="c",
                    reveal=True,
                    size=27,
                )
            ],
            [
                A("lines", "c", at="cab", to=2),
                A("lines", "c", at="reg", to=4),
                A("lines", "c", at="ops", to=4),
                A("lines", "c", at="gate", to=7),
                A("hl", "c", at="gate", lines=[5, 6]),
            ],
        ),
        beat(
            "inspeccion",
            ("", "Inspeccionar y ejecutar"),
            """El modo inspección simula el circuito capa por capa, para que veas cómo evoluciona el estado; mientras está activo no se pueden añadir operaciones.
             [[seed]]La aleatoriedad de las visualizaciones viene de una semilla, que puedes ver y cambiar en el menú Edit.
             [[run]]Para ejecutar en hardware, pulsa Run circuit, elige un procesador y una instancia, que depende de tu plan, y el número de disparos. Si no eliges, se envía al procesador menos ocupado.
             [[res]]Los resultados aparecen en la tabla Workloads de IBM Quantum Platform, con el circuito original y el transpilado, el histograma y el código.""",
            [
                Flow(
                    [
                        dict(t="Run circuit", s="QPU · instancia · disparos · etiquetas"),
                        dict(t="Workloads", s="estado del trabajo"),
                        dict(t="Resultados", s="circuito transpilado · histograma · código"),
                    ],
                    id="f",
                    stagger=True,
                ),
                T("sin elegir QPU → el menos ocupado", "note", id="n", hidden=True),
            ],
            [
                A("item", "f", at="run", i=0),
                A("show", "n", at="run", t=2),
                A("item", "f", at="res", i=1),
                A("item", "f", at="res", t=1, i=2),
            ],
        ),
        beat(
            "disco",
            ("", "El disco de fase"),
            """Las visualizaciones necesitan un poco de teoría. El estado de un qubit se puede escribir con dos números: la probabilidad p de encontrarlo en uno, y una fase fi.
             [[disco]]El disco de fase dibuja p como el relleno azul del disco, y la fase como una línea desde el centro hasta el borde.
             [[pur]]Para varios qubits, el anillo negro indica la pureza reducida: vale uno si el qubit no está entrelazado con los demás, y baja hasta un medio si lo está al máximo.
             [[bloch]]El disco contiene toda la información de la esfera de Bloch, y se puede convertir a sus coordenadas.""",
            [
                M(r"|\psi\rangle=\sqrt{1-p}\,|0\rangle+e^{i\varphi}\sqrt{p}\,|1\rangle", size=44),
                Row(
                    Box(
                        "def",
                        "Disco de fase",
                        L(
                            [
                                "relleno azul: $p$",
                                "línea: fase $\\varphi$",
                                "anillo: pureza reducida $\\in[\\tfrac12,1]$",
                            ],
                            size=27,
                        ),
                        id="d",
                        hidden=True,
                    ),
                    Box(
                        "idea",
                        "A la esfera de Bloch",
                        M(
                            r"x=2\sqrt{p(1-p)}\cos\varphi\\ y=2\sqrt{p(1-p)}\sin\varphi\\ z=1-2p",
                            size=30,
                        ),
                        id="b",
                        hidden=True,
                    ),
                    gap=26,
                ),
            ],
            [A("show", "d", at="disco"), A("show", "b", at="bloch")],
        ),
        beat(
            "pred_vistas",
            ("", "Antes de ver las vistas"),
            """Antes de ver las visualizaciones, apuesta. Tomemos un circuito de dos qubits: una Hadamard en cada uno y una puerta CZ. Las dos Hadamard dejan los cuatro estados con la misma probabilidad.
             [[cual]]¿Qué crees que hará la CZ con esas probabilidades?""",
            [Circ(2, [G("h", 0), G("h", 1), G("cz", 0, 1)])],
            ask=predict(
                "Después de la CZ, ¿cómo quedan las probabilidades de `00`, `01`, `10` y `11`?",
                [
                    "las cuatro siguen en 1/4",
                    "`11` sube a 1/2 y las otras bajan",
                    "`11` baja a 0",
                    "solo quedan `00` y `11`",
                ],
                "Anotado. Veamos las vistas.",
            ),
        ),
        beat(
            "vistas",
            ("", "Probabilidades, vector de estado y q-esfera"),
            """Las otras tres vistas muestran el estado de todos los qubits juntos. Tomemos este circuito: Hadamard en los dos qubits y una CZ.
             [[prob]]La vista de probabilidades: barras con la probabilidad de cada estado de la base, hasta ocho qubits. Aquí, un cuarto para cada uno: la CZ no cambió ninguna probabilidad, y si apostaste por eso, acertaste. No muestra fases.
             [[sv]]La vista de vector de estado, hasta seis qubits, muestra las amplitudes: la altura es el módulo y el color, la fase. Aquí todas miden un medio, pero uno uno tiene fase pi: un signo menos.
             [[qs]]Y la q-esfera, hasta cinco qubits, pone cada estado de la base en una esfera: cero cero en el polo norte, uno uno en el sur, y los demás en paralelos según cuántos unos tienen. El tamaño de cada nodo es la probabilidad y el color, la fase.""",
            [
                Row(
                    Circ(2, [G("h", 0), G("h", 1), G("cz", 0, 1)], id="q"),
                    M(
                        r"\tfrac12\big(|00\rangle+|01\rangle+|10\rangle\red{-}|11\rangle\big)",
                        size=36,
                    ),
                    gap=30,
                ),
                Hist(
                    [["00", 0.25], ["01", 0.25], ["10", 0.25], ["11", 0.25]],
                    id="h",
                    prob=True,
                    ymax=0.4,
                    h=130,
                    grow=True,
                    hidden=True,
                ),
                Table(
                    ["Vista", "Muestra", "Límite"],
                    [
                        ["Probabilidades", "$p_k$ (sin fases)", "8 qubits"],
                        ["Vector de estado", "módulo y fase de cada amplitud", "6 qubits"],
                        ["Q-esfera", "nodos: tamaño = $p_k$, color = fase", "5 qubits"],
                    ],
                    id="t",
                    stagger=True,
                    size=21,
                ),
            ],
            [
                A("show", "h", at="prob"),
                A("grow", "h", at="prob"),
                A("item", "t", at="prob", i=0),
                A("item", "t", at="sv", i=1),
                A("item", "t", at="qs", i=2),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Mira otra vez el estado de este circuito.""",
            [M(r"\tfrac12\big(|00\rangle+|01\rangle+|10\rangle-|11\rangle\big)", size=44)],
            ask=choice(
                "En la vista de vector de estado, ¿qué fase relativa tiene la amplitud de $|11\\rangle$?",
                ["$0$", "$\\pi/2$", "$\\pi$", "$3\\pi/2$"],
                2,
                "Correcto: $-1=e^{i\\pi}$. Su barra tiene la misma altura que las demás, pero otro color.",
                wrong=[
                    "Las otras tres tienen fase 0; esta tiene un signo menos.",
                    "$e^{i\\pi/2}=i$, no $-1$.",
                    None,
                    "$e^{3i\\pi/2}=-i$, no $-1$.",
                ],
            ),
        ),
        beat(
            "glosario",
            ("", "Glosario de operaciones"),
            """Composer agrupa sus operaciones por familias. [[clas]]Las clásicas: NOT o X, CNOT, Toffoli, SWAP e identidad. [[fase]]Las de fase: Z, S, T, sus inversas, la puerta de fase P y RZ; recuerda que P de pi es Z, P de pi medios es S y P de pi cuartos es T.
             [[h]]La Hadamard, que crea superposiciones. [[cu]]Las demás puertas cuánticas: raíz de X y su inversa, Y, RX, RY, RXX, RZZ, la U general de tres parámetros, y las Toffoli simplificadas, RCCX y RC3X, iguales a Toffoli salvo fases relativas.
             [[nou]]Y las no unitarias, que no son reversibles: reset, que devuelve el qubit a cero, y la medición en la base Z. [[mod]]Más el modificador de control y la barrera, que impide que el compilador combine puertas a través de ella.""",
            [
                Table(
                    ["Familia", "Operaciones"],
                    [
                        ["Clásicas", "X (NOT) · CX · CCX (Toffoli) · SWAP · I"],
                        [
                            "Fase",
                            "Z · S · T · S† · T† · $P(\\theta)$ · $R_Z(\\theta)$ — $P(\\pi)=Z$, $P(\\tfrac\\pi2)=S$, $P(\\tfrac\\pi4)=T$",
                        ],
                        ["Hadamard", "H: $|0\\rangle\\to|+\\rangle$, $|1\\rangle\\to|-\\rangle$"],
                        [
                            "Cuánticas",
                            "√X · √X† · Y · RX · RY · RXX · RZZ · U(θ,φ,λ) · RCCX · RC3X",
                        ],
                        ["No unitarias", "reset · measure"],
                        ["Modificadores", "control · barrier"],
                    ],
                    id="t",
                    stagger=True,
                    size=23,
                )
            ],
            [
                A("item", "t", at="clas", i=0),
                A("item", "t", at="fase", i=1),
                A("item", "t", at="h", i=2),
                A("item", "t", at="cu", i=3),
                A("item", "t", at="nou", i=4),
                A("item", "t", at="mod", i=5),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Una pregunta sobre las puertas de fase.""",
            [M(r"P(\theta)=\begin{pmatrix}1&0\\0&e^{i\theta}\end{pmatrix}", size=44)],
            ask=choice(
                "¿Qué ángulo hace que $P(\\theta)$ sea la puerta T?",
                ["$\\pi$", "$\\pi/2$", "$\\pi/4$", "$\\pi/8$"],
                2,
                "Correcto: $T=P(\\pi/4)$. Y $S=P(\\pi/2)=T^2$, $Z=P(\\pi)=S^2$.",
                wrong=[
                    "$P(\\pi)$ es Z.",
                    "$P(\\pi/2)$ es S.",
                    None,
                    "Cuidado: a T a veces se la llama «puerta π/8» porque, salvo una fase global, es $R_Z(\\pi/4)$ y se escribe con $e^{\\mp i\\pi/8}$; pero como puerta de fase es $P(\\pi/4)$.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. Composer corre en la web, así que el cuaderno de práctica usa el mismo OpenQASM, ejecutado en tu equipo. Ábrelo con el comando de abajo. [[n1]]Primero ejecutas el programa con una puerta propia.
             [[n2]]Después cambias una CZ por una fase controlada y compruebas que las probabilidades no se mueven, pero la amplitud sí. [[n3]]Y por último defines tu propia puerta GHZ. [[check]]Cada misión tiene una comprobación que se actualiza sola: busca la marca verde.""",
            [
                Mission(
                    "practica/p1-composer.py",
                    [
                        (1, "Ejecuta el OpenQASM con la puerta propia `bell` y lee los conteos."),
                        (
                            2,
                            r"Cambia la `cz` por `cu1(pi/2)`: la amplitud de $|11\rangle$ pasa a $i/2$ y las probabilidades no cambian.",
                        ),
                        (3, "Define en OpenQASM una puerta `ghz a, b, c` para tres qubits."),
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
            """Antes de cerrar, dos preguntas para pensar. No hay respuesta automática: escribe con tus palabras. Lo que escribas se guarda y lo verás cuando vuelvas a esta lección.""",
            [T("Explicar con tus palabras es la mejor prueba de que entendiste.", "subtitle")],
            ask=reflect(
                "La vista de probabilidades no muestra fases. ¿En qué situación te engañaría mirar solo esa vista? Explícalo con un ejemplo.",
                "¿Cuándo preferirías construir un circuito arrastrando puertas y cuándo escribiéndolo en código? Piensa en un ejemplo de cada caso.",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Composer construye circuitos arrastrando puertas o escribiendo OpenQASM dos. [[r2]]El modo inspección muestra la evolución capa por capa. [[r3]]Run circuit envía el trabajo a un QPU y los resultados aparecen en Workloads.
             [[r4]]Y sus visualizaciones, disco de fase, probabilidades, vector de estado y q-esfera, muestran el estado desde ángulos distintos.""",
            [
                L(
                    [
                        "arrastrar y soltar u OpenQASM 2.0",
                        "modo inspección: capa por capa",
                        "Run circuit → Workloads",
                        "disco de fase · probabilidades · vector de estado · q-esfera",
                    ],
                    id="r",
                    stagger=True,
                )
            ],
            [
                A("item", "r", at="r1", i=0),
                A("item", "r", at="r2", i=1),
                A("item", "r", at="r3", i=2),
                A("item", "r", at="r4", i=3),
            ],
        ),
    ],
    sources=["composer"],
    practice=[
        "Abre [Composer](https://quantum.cloud.ibm.com/composer), construye el estado de Bell y compara su q-esfera con la del circuito H, H, CZ.",
        "Escribe en el editor de OpenQASM una puerta propia `ghz a, b, c` y úsala en un circuito de tres qubits.",
    ],
)

s_cierre, a_cierre = resumen(
    [
        "todo programa sigue cuatro pasos: mapear, optimizar, ejecutar y posprocesar",
        "un circuito ISA usa las puertas base y la conectividad del chip",
        "en un GHZ los tres qubits coinciden siempre",
        "un paso de Trotter aplica `rzz` y después `rx`, con ángulos de $2\\cdot J\\,dt$ y $2\\cdot h\\,dt$",
    ]
)
cierre = lesson(
    "p1-cierre",
    "Cierre de la Parte I: repaso y un paso de Trotter",
    "Un repaso corto de la Parte uno y el primer paso del proyecto Ising: el circuito de un paso de Trotter.",
    [
        "recordar el patrón de cuatro pasos, qué es un circuito ISA y cómo se correlacionan los qubits de un GHZ",
        "escribir el circuito de un paso de Trotter para dos espines",
    ],
    [
        beat(
            "repaso1",
            ("", "Repaso: el patrón"),
            """Tres preguntas rápidas de la Parte uno, y después una función del proyecto Ising. La primera, sobre el flujo de trabajo.""",
            [T("Mapear · Optimizar · Ejecutar · Posprocesar", "subtitle")],
            ask=choice(
                "Tienes un circuito abstracto con una Hadamard y una CNOT, y quieres que el chip de IBM lo ejecute. ¿En qué paso del patrón lo adaptas a las puertas y la conectividad del chip?",
                ["Mapear", "Optimizar", "Ejecutar", "Posprocesar"],
                1,
                "Correcto: el paso de optimizar produce el circuito ISA, con las puertas base y los pares de qubits que el chip permite.",
                wrong=[
                    "Mapear solo expresa el problema como circuitos y operadores.",
                    None,
                    "Ejecutar recibe un circuito que ya debe ser ISA.",
                    "Posprocesar trabaja con resultados, no con circuitos.",
                ],
            ),
        ),
        beat(
            "repaso2",
            ("", "Repaso: GHZ"),
            """Segunda pregunta, sobre el estado GHZ de tres qubits.""",
            [
                Circ(
                    3,
                    [
                        G("h", 0),
                        G("cx", 0, 1),
                        G("cx", 1, 2),
                        G("barrier"),
                        G("measure", 0, c=0),
                        G("measure", 1, c=1),
                        G("measure", 2, c=2),
                    ],
                    clbits=3,
                    creg="meas",
                )
            ],
            ask=numeric(
                "Mides el circuito muchas veces. ¿Cuántas cadenas de bits distintas aparecen?",
                2,
                "Correcto: solo `000` y `111`, porque las dos CNOT copian el valor del qubit 0 a los otros dos.",
                tol=0,
                hint="Los tres qubits coinciden siempre.",
            ),
        ),
        beat(
            "repaso3",
            ("", "Repaso: Estimator"),
            """Tercera pregunta, sobre las primitivas.""",
            [T("Sampler → cadenas de bits · Estimator → valores esperados", "subtitle")],
            ask=choice(
                "Quieres el valor esperado de $Z_0Z_1$ en el estado de Bell. ¿Qué primitiva usas?",
                ["Sampler", "Estimator"],
                1,
                "Correcto: Estimator devuelve el valor esperado de un observable directamente; con Sampler tendrías que reconstruirlo a partir de las cadenas de bits.",
                wrong=["Sampler devuelve cadenas de bits, no valores esperados."],
            ),
        ),
        beat(
            "paso",
            ("", "Tu turno"),
            """Ahora el primer paso del proyecto Ising. [[ej]]Dos espines, un campo y un acoplamiento: te toca escribir el circuito de un solo paso de tiempo. [[n]]Se compara con el paso exacto de Trotter, calculado con matrices.""",
            [
                Exercise(
                    "p1-cierre/paso-trotter",
                    r"Completa `paso_trotter(J, h, dt)`: `J` es el acoplamiento, `h` el campo y `dt` el paso de tiempo. Devuelve un circuito de 2 qubits con una `rzz` entre los dos y después una `rx` en cada uno, de modo que sea el paso de Trotter de $H = J\,Z_0Z_1 + h\,(X_0 + X_1)$. Ojo: `rzz(θ, a, b)` aplica $e^{-i\frac{θ}{2}Z_aZ_b}$ y `rx(θ, q)` aplica $e^{-i\frac{θ}{2}X_q}$, así que el ángulo que escribes no es $J\,dt$ a secas.",
                    level=3,
                    id="e1",
                    hidden=True,
                    hints=[
                        "Compara el exponente que quieres con el que aplica la puerta: el ángulo es un múltiplo de $J\\,dt$ o de $h\\,dt$.",
                        "Son tres líneas: el ángulo de la `rzz` depende de `J` y `dt`; los de las dos `rx`, de `h` y `dt`.",
                        "Cada ángulo es un producto de tres factores; la `rzz` y las `rx` llevan el mismo número delante.",
                    ],
                )
            ],
            [A("show", "e1", at="ej")],
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen de la parte. [[r1]]Todo programa sigue cuatro pasos. [[r2]]En hardware solo se ejecutan circuitos ISA. [[r3]]En un GHZ, los tres qubits coinciden siempre.
             [[r4]]Y un paso de Trotter aplica una rzz y después una rx por espín. Con esto cierras la Parte uno; en la siguiente, los circuitos a fondo.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[],
    practice=[
        "Ejecuta `paso_trotter(1.0, 0.5, 0.1)` con `Statevector` y compara su estado con el de la evolución exacta de $H$."
    ],
)

LESSONS = [que_es, patrones, instalar, quickstart, composer, cierre]
