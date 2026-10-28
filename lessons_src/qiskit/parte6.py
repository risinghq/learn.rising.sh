"""Parte VI · Ruido: supresión y mitigación."""

from lib import (
    A,
    Box,
    Circ,
    Code,
    Flow,
    G,
    Graph,
    Hist,
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

# ------------------------------------------------------------------ 6.1 Panorama
s_panorama, a_panorama = resumen(
    [
        "ruido: diferencia entre el circuito ideal y el resultado medido",
        "suprimir cambia la ejecución; mitigar corrige sesgos con más circuitos",
        "aprender caracteriza el ruido; postseleccionar descarta muestras sospechosas",
        "cada técnica cuesta tiempo y disparos, y ninguna sirve para todo circuito",
    ]
)
panorama = lesson(
    "p6-panorama",
    "Panorama de la gestión del ruido",
    "De dónde vienen los errores y cómo elegir entre supresión, mitigación, aprendizaje del ruido y postselección.",
    [
        "distinguir supresión de mitigación",
        "relacionar cada técnica con el tipo de resultado que mejora",
        "reconocer el costo y los límites de una estrategia",
    ],
    [
        beat(
            "intro",
            ("", "El resultado ideal y el que medimos"),
            """Un circuito cuántico define una evolución ideal, pero el dispositivo físico no la reproduce exactamente. [[ideal]]Si el circuito prepara un estado de Bell, en el caso ideal solo medimos cero cero o uno uno, con la misma probabilidad. [[ruido]]En un computador real también aparecen otros resultados: el ruido desvió parte de las mediciones.
             [[meta]]Gestionar el ruido consiste en reducir esa diferencia. No existe una sola corrección universal: hay técnicas que cambian cómo se ejecuta el circuito, otras que procesan varias ejecuciones y otras que descartan muestras sospechosas.""",
            [
                T("Una misma preparación, dos distribuciones", "title"),
                Row(
                    Box("def", "Ideal", T("solo `00` y `11` · mitad y mitad", "body"), id="a"),
                    Box(
                        "warn",
                        "Con ruido",
                        T("también aparecen `01` y `10`", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=24,
                ),
            ],
            [A("show", "a", at="ideal"), A("show", "b", at="ruido")],
        ),
        beat(
            "fuentes",
            ("", "¿De dónde vienen los errores?"),
            """El ruido agrupa varios fenómenos físicos y de lectura. [[puertas]]Las puertas tienen errores: una rotación puede quedar un poco desviada, y las puertas de dos qubits suelen ser especialmente sensibles. [[lectura]]La lectura puede confundir cero con uno.
             [[coherencia]]Además, mientras un qubit espera, pierde coherencia; y los qubits cercanos pueden influirse entre sí. [[deriva]]Por último, el dispositivo cambia con el tiempo: una calibración describe un momento, no una verdad permanente.""",
            [
                Table(
                    ["Origen", "Qué se observa"],
                    [
                        ["Puertas", "la operación se desvía de la ideal"],
                        ["Lectura", "se registra otro bit"],
                        ["Espera", "decoherencia durante intervalos inactivos"],
                        [
                            "Acoplamiento y deriva",
                            "qubits vecinos y calibración cambian el resultado",
                        ],
                    ],
                    id="t",
                    stagger=True,
                    size=23,
                )
            ],
            [
                A("item", "t", at="puertas", i=0),
                A("item", "t", at="lectura", i=1),
                A("item", "t", at="coherencia", i=2),
                A("item", "t", at="deriva", i=3),
            ],
        ),
        beat(
            "familias",
            ("", "Cuatro maneras de responder"),
            """Podemos responder de cuatro maneras. [[suprimir]]Suprimir es reducir la acumulación del error durante la ejecución, por ejemplo, insertar pulsos en esperas o aleatorizar las puertas.
             [[mitigar]]Mitigar es ejecutar variantes y combinar sus resultados para estimar uno menos sesgado. [[aprender]]Aprender el ruido es medir cómo se comporta el dispositivo para guiar una mitigación. [[filtrar]]Y postseleccionar es descartar las muestras que no pasan ciertos controles.""",
            [
                Flow(
                    [
                        dict(t="Suprimir", s="cambiar la ejecución", color="blue"),
                        dict(t="Mitigar", s="combinar varias ejecuciones", color="gold"),
                        dict(t="Aprender", s="caracterizar capas y mediciones"),
                        dict(t="Postseleccionar", s="filtrar muestras", color="red"),
                    ],
                    id="f",
                    stagger=True,
                    vertical=True,
                )
            ],
            [
                A("item", "f", at="suprimir", i=0),
                A("item", "f", at="mitigar", i=1),
                A("item", "f", at="aprender", i=2),
                A("item", "f", at="filtrar", i=3),
            ],
        ),
        beat(
            "costo",
            ("", "Precisión también cuesta"),
            """Las técnicas compran calidad con recursos. [[mas]]Más variantes suelen significar más circuitos, más disparos y más tiempo de procesador. [[sesgo]]Una estimación corregida puede reducir sesgo, pero no elimina la incertidumbre estadística.
             [[limite]]Y hay un límite fundamental: si el circuito ya produce resultados casi aleatorios por el ruido, ninguna extrapolación puede reconstruir información que se perdió. Primero conviene diseñar y compilar un circuito razonable.""",
            [
                Flow(
                    [
                        dict(t="Calidad buscada"),
                        dict(t="más ejecuciones", s="circuitos, disparos, tiempo", color="gold"),
                        dict(t="límite", s="circuito demasiado ruidoso", color="red"),
                    ],
                    id="g",
                ),
                Box(
                    "idea",
                    "Empieza por el circuito",
                    T(
                        "menos profundidad y menos puertas de dos qubits ayudan antes de mitigar",
                        "body",
                    ),
                    id="n",
                    hidden=True,
                ),
            ],
            [A("show", "n", at="limite")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Una pregunta sobre las cuatro respuestas al ruido.""",
            [
                T(
                    "Quieres convertir errores coherentes difíciles de modelar en un canal de Pauli más sencillo.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué técnica se ajusta a esa idea?",
                ["desacoplamiento dinámico", "ZNE", "twirling de Pauli"],
                2,
                "Correcto: el twirling aleatoriza las puertas y adapta la estructura del ruido; no elimina todas las fuentes de error.",
                wrong=[
                    "El desacoplamiento actúa sobre qubits inactivos.",
                    "ZNE extrapola resultados medidos a ruido cero.",
                    None,
                ],
            ),
        ),
        beat(
            "predice",
            ("", "Antes de medir el ruido"),
            """Pongamos un número al ruido. Preparamos el estado de Bell en un simulador con un modelo de ruido sencillo. [[cx]]Cada CNOT tiene un uno por ciento de error despolarizante. [[lectura]]Y cada lectura se equivoca un dos por ciento de las veces.
             [[apuesta]]Se miden cuatro mil disparos. Un Bell ideal solo da cero cero y uno uno: apuesta cuántos disparos serán cero uno o uno cero.""",
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
            [],
            ask=predict(
                "¿Cuántos de los 4000 disparos serán `01` o `10`?",
                [
                    "ninguno: el circuito es correcto",
                    "unos 40 (1 %)",
                    "unos 170 (4 %)",
                    "unos 800 (20 %)",
                ],
                "Anotado. Ejecutémoslo y contemos.",
            ),
        ),
        beat(
            "ruido_real",
            ("", "El Bell sale sucio"),
            """Este es el modelo y el resultado. [[modelo]]Un NoiseModel de Aer con error despolarizante en cada cx y un error de lectura simétrico.
             [[run]]Lo ejecutamos con una semilla fija, para que el número no cambie entre ejecuciones. [[res]]Salen unos ciento setenta disparos erróneos: un cuatro coma tres por ciento.
             [[suma]]No es el uno por ciento de la CNOT: se suman el error de la puerta y los de lectura de los dos qubits. Si apostaste por ninguno, ahora ves por qué hace falta toda esta parte del curso.""",
            [
                Code(
                    """from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error

modelo = NoiseModel()
modelo.add_all_qubit_quantum_error(depolarizing_error(0.01, 2), ["cx"])
modelo.add_all_qubit_readout_error(ReadoutError([[0.98, 0.02], [0.02, 0.98]]))

bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)
bell.measure_all()

sim = AerSimulator(noise_model=modelo, seed_simulator=7)
cuentas = sim.run(bell, shots=4000).result().get_counts()
print(dict(sorted(cuentas.items())))
print(f"disparos erróneos: {(cuentas['01'] + cuentas['10']) / 4000:.1%}")""",
                    id="c",
                    size=19,
                ),
                Out(
                    "{'00': 1912, '01': 79, '10': 94, '11': 1915}\ndisparos erróneos: 4.3%",
                    id="o",
                    hidden=True,
                    check=True,
                ),
                Hist(
                    [["00", 1912], ["01", 79], ["10", 94], ["11", 1915]],
                    id="h",
                    hidden=True,
                    h=130,
                    w=520,
                    ymax=2200,
                    color="red",
                ),
            ],
            [
                A("hl", "c", at="modelo", range="5-7"),
                A("hl", "c", at="run", range="14-15"),
                A("hl", "c", at="res", range="16-17"),
                A("show", "o", at="res"),
                A("show", "h", at="res"),
                A("grow", "h", at="res"),
            ],
        ),
        beat(
            "simular",
            ("", "Simular no es medir el QPU"),
            """Una simulación con ruido es útil para experimentar, pero responde una pregunta distinta. [[aer]]En Aer eliges un modelo y ves cómo ese modelo afecta al circuito. [[real]]En un QPU intervienen ruido, calibraciones, deriva y efectos que quizá no incluya tu simulador.
             [[puente]]Por eso la simulación sirve para depurar y comparar hipótesis, no para prometer que una mitigación dará la misma mejora en hardware. Las lecciones siguientes muestran las herramientas del servicio y cuándo usarlas.""",
            [
                Row(
                    Box("def", "Aer", T("resultado bajo un modelo que tú defines", "body"), id="a"),
                    Box(
                        "idea",
                        "QPU",
                        T("ruido físico que cambia con el dispositivo y el tiempo", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=20,
                )
            ],
            [A("show", "a", at="aer"), A("show", "b", at="real")],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Una pregunta para ordenar el mapa.""",
            [
                Flow(
                    [
                        dict(t="suprimir"),
                        dict(t="mitigar"),
                        dict(t="aprender"),
                        dict(t="postseleccionar"),
                    ],
                    id="f",
                )
            ],
            ask=numeric(
                "¿Cuántas familias de respuesta acabamos de distinguir?",
                4,
                "Son cuatro: suprimir, mitigar, aprender el ruido y postseleccionar.",
                tol=0,
                hint="Cuenta las cuatro etiquetas del mapa.",
                solution="4",
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. Abre el cuaderno de práctica con el comando de abajo. [[n1]]Primero reproduces el Bell ruidoso y cuentas sus disparos erróneos. [[n2]]Después subes el error de la CNOT hasta que más del doce por ciento de las muestras salga mal. [[n3]]Y por último escribes la distancia entre la distribución medida y la ideal, la cifra con la que compararás todas las técnicas de esta parte.
             [[check]]Cada misión tiene una comprobación: busca la marca verde.""",
            [
                Mission(
                    "practica/p6-panorama.py",
                    [
                        (1, "Ejecuta el Bell con ruido y mide la fracción de `01` y `10`."),
                        (2, "Sube el error de la CNOT hasta superar el 12 % de disparos erróneos."),
                        (
                            3,
                            "Escribe `distancia_tv(medida, ideal)`, la distancia de variación total entre dos distribuciones.",
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
            """Dos preguntas para pensar con calma, conectadas con lo que viste en el cuaderno.""",
            [T("Antes de mitigar, mide cuánto ruido hay.", "subtitle")],
            ask=reflect(
                "Con un 1 % de error por CNOT y un 2 % de lectura, el Bell salió con un 4 % de disparos erróneos. ¿Qué crees que pasaría con un circuito de 50 CNOT? ¿Qué cifra mirarías para saberlo?",
                "De las cuatro respuestas (suprimir, mitigar, aprender, postseleccionar), ¿cuál probarías primero en tu cadena de Ising y por qué?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]El ruido nace en las puertas, la lectura, las esperas y la interacción entre qubits; además, deriva con el tiempo.
             [[r2]]Suprimir cambia la ejecución; mitigar combina resultados; aprender caracteriza el ruido; postseleccionar filtra muestras.
             [[r3]]Cada técnica agrega costo y ninguna recupera información que el circuito perdió por completo.
             [[r4]]Simular con ruido ayuda a explorar, pero no reemplaza una medición en hardware.""",
            s_panorama,
            a_panorama,
        ),
    ],
    sources=["error-mitigation-overview"],
    practice=[
        "Toma un circuito que ya conozcas y anota si tu objetivo es mejorar una expectativa, una distribución de muestras o el tiempo de espera de un qubit."
    ],
)


# ------------------------------------------------------------------ 6.2 Supresión
s_supresion, a_supresion = resumen(
    [
        "desacoplamiento dinámico: pulsos que llenan esperas y cancelan parte del acoplamiento",
        "los pulsos insertados equivalen a identidad en el caso ideal",
        "twirling: conjunto aleatorio de circuitos con la misma operación ideal",
        "más randomizations y shots pueden subir el costo",
    ]
)
supresion = lesson(
    "p6-supresion",
    "Supresión: desacoplamiento dinámico y twirling",
    "Reducir el efecto del ruido durante la ejecución con pulsos de desacoplamiento dinámico y twirling de Pauli.",
    [
        "explicar para qué sirven las secuencias de desacoplamiento dinámico",
        "describir qué cambia el twirling y qué conserva",
        "activar ambas opciones en las primitivas del lado del cliente",
    ],
    [
        beat(
            "intro",
            ("", "Reducir antes de medir"),
            """La supresión intenta que el circuito sufra menos ruido antes de leer el resultado. [[dos]]Veremos dos técnicas que el servicio puede aplicar al ejecutar: desacoplamiento dinámico y twirling de Pauli.
             [[limite]]No son puertas mágicas que se agregan sin costo. Introducen pulsos o variantes de circuito; pueden ayudar en el caso adecuado y empeorar un circuito que ya está muy ocupado.""",
            [
                Row(
                    Box("idea", "Desacoplamiento dinámico", T("ocupa las esperas", "body"), id="a"),
                    Box(
                        "idea", "Twirling", T("aleatoriza las puertas", "body"), id="b", hidden=True
                    ),
                    gap=24,
                )
            ],
            [A("show", "a", at="dos"), A("show", "b", at="dos")],
        ),
        beat(
            "esperas",
            ("", "Desacoplamiento dinámico"),
            """Al programar el circuito, un qubit puede pasar un rato sin puertas mientras otros siguen trabajando. [[idle]]Durante esa espera, interacciones no deseadas pueden acumular un error de fase.
             [[pulsos]]El desacoplamiento dinámico inserta una secuencia de pulsos en ese hueco. La secuencia está construida para que, en el caso ideal, el conjunto equivalga a identidad; físicamente, ayuda a cancelar parte de la interacción no deseada.""",
            [
                Flow(
                    [
                        dict(t="puerta"),
                        dict(t="espera", s="el qubit queda inactivo", color="gold"),
                        dict(t="X · X", s="secuencia de identidad", color="blue"),
                        dict(t="siguiente puerta"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [A("item", "f", at="idle", i=1), A("item", "f", at="pulsos", i=2)],
        ),
        beat(
            "predice_dd",
            ("", "Antes de rellenar los huecos"),
            """Probémoslo en un circuito de tres qubits, transpilado para un backend falso de cinco qubits. [[circ]]Hay una H, tres CNOT entre los qubits cero y uno, una CNOT entre uno y dos, y una H final. Mientras los qubits cero y uno trabajan, el dos espera; y al final, espera el cero.
             [[apuesta]]Rellenaremos los huecos con la secuencia XX. Apuesta: ¿cuántos pulsos X se añaden en total, y cambia la operación del circuito?""",
            [
                Circ(
                    3,
                    [
                        G("h", 0),
                        G("cx", 0, 1),
                        G("cx", 0, 1),
                        G("cx", 0, 1),
                        G("cx", 1, 2),
                        G("h", 2),
                    ],
                )
            ],
            [],
            ask=predict(
                "Al rellenar con XX, ¿qué esperas?",
                [
                    "ningún pulso: no hay huecos",
                    "2 pulsos X y la misma operación",
                    "4 pulsos X y la misma operación",
                    "2 pulsos X y una operación distinta",
                ],
                "Anotado. Programamos el circuito y contamos.",
            ),
        ),
        beat(
            "dd_codigo",
            ("", "Programar y rellenar"),
            """El código. [[isa]]Transpilamos el circuito con el layout fijo, sin optimizar, para que las esperas sean las del circuito original. [[pm]]El gestor de pases programa el circuito con ALAPScheduleAnalysis y PadDynamicalDecoupling rellena los huecos con la secuencia de dos puertas X.
             [[res]]Se añaden dos pulsos X, y la operación es la misma: Operator equiv da verdadero. El desacoplamiento solo rellena esperas con una identidad; que sirva en un dispositivo real depende de lo bien calibrados que estén esos pulsos.""",
            [
                Code(
                    """from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import XGate
from qiskit.quantum_info import Operator
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDynamicalDecoupling
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

fake = FakeManilaV2()
logico = QuantumCircuit(3)
logico.h(0)
for _ in range(3):
    logico.cx(0, 1)
logico.cx(1, 2)
logico.h(2)
isa = transpile(logico, fake, optimization_level=0, initial_layout=[0, 1, 2], seed_transpiler=1)

pm = PassManager([ALAPScheduleAnalysis(target=fake.target),
                  PadDynamicalDecoupling(target=fake.target, dd_sequence=[XGate(), XGate()])])
con_dd = pm.run(isa)

def pulsos_x(qc):
    return sum(1 for inst in qc.data if inst.operation.name == "x")

print("pulsos X añadidos:", pulsos_x(con_dd) - pulsos_x(isa))
print("misma operación:", Operator(isa).equiv(Operator(con_dd)))""",
                    id="c",
                    size=17,
                ),
                Out("pulsos X añadidos: 2\nmisma operación: True", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="isa", lines=[15]),
                A("hl", "c", at="pm", range="17-19"),
                A("show", "o", at="res"),
                A("hl", "c", at="res", range="24-25"),
            ],
        ),
        beat(
            "secuencias",
            ("", "La secuencia depende del dispositivo"),
            """No hay una única secuencia mejor para todos los circuitos. [[xx]]La secuencia XX inserta dos pulsos X durante la espera. [[xp]]La secuencia XpXm usa dos rotaciones X de signos opuestos.
             [[opciones]]En la opción `sequence_type` puedes elegir la secuencia que admita el servicio. La duración y la calibración de los pulsos importan: la identidad matemática no convierte pulsos imperfectos en pulsos perfectos.""",
            [
                Table(
                    ["Opción", "Idea"],
                    [
                        ["`XX`", "dos pulsos X durante el intervalo inactivo"],
                        ["`XpXm`", "rotaciones X positivas y negativas"],
                        ["XY4", "secuencia más larga que intercala X e Y"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                )
            ],
            [
                A("item", "t", at="xx", i=0),
                A("item", "t", at="xp", i=1),
                A("item", "t", at="opciones", i=2),
            ],
        ),
        beat(
            "cuando",
            ("", "No sirve igual para todo circuito"),
            """El desacoplamiento dinámico es más prometedor cuando hay huecos largos y qubits inactivos. [[huecos]]Si las operaciones ya llenan casi todo el tiempo, puede no haber nada que proteger.
             [[peor]]Y si los pulsos insertados tienen errores importantes, añadirlos puede empeorar el resultado. Por eso conviene comparar en un problema pequeño y mirar tanto la calidad como el tiempo de ejecución.""",
            [
                Row(
                    Box("def", "Hay esperas", T("probar una secuencia y medir", "body"), id="a"),
                    Box(
                        "warn",
                        "Circuito denso",
                        T("los pulsos pueden agregar error", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=24,
                )
            ],
            [A("show", "a", at="huecos"), A("show", "b", at="peor")],
        ),
        beat(
            "twirling",
            ("", "Twirling de Pauli"),
            """El twirling agrega puertas de Pauli elegidas al azar antes y después de ciertas puertas, normalmente de dos qubits. [[igual]]Las Paulis se eligen en pares para que la operación ideal total se conserve.
             [[canal]]En cambio, cambia la representación del ruido: al promediar las variantes, un error coherente difícil puede comportarse como un canal de Pauli. [[promedio]]La salida reúne muestras de muchos circuitos aleatorizados; el promedio reduce sensibilidad a algunas coherencias, con el costo de más variantes.""",
            [
                M(r"P_L\,G\,P_R = G", size=48, id="eq"),
                Table(
                    ["Se conserva", "Se aleatoriza"],
                    [
                        ["la puerta ideal `G`", "cómo se distribuye el ruido"],
                        ["el objetivo del circuito", "qué variante aporta cada disparo"],
                    ],
                    id="t",
                    hidden=True,
                    stagger=True,
                    size=24,
                ),
            ],
            [A("show", "eq", at="igual"), A("show", "t", at="canal")],
        ),
        beat(
            "predice_tw",
            ("", "Antes de aleatorizar"),
            """Comprobemos que el twirling conserva la operación ideal. [[idea]]Para cada variante elegimos una Pauli al azar, la ponemos antes de la CNOT, y ponemos después la Pauli que resulta de empujarla a través de la CNOT.
             [[apuesta]]Generamos cuarenta variantes. Apuesta: ¿cuántas implementan exactamente la misma operación que una CNOT sola?""",
            [Circ(2, [G("box", 0, 1, label="P_L"), G("cx", 0, 1), G("box", 0, 1, label="P_R")])],
            [],
            ask=predict(
                "De 40 variantes aleatorias, ¿cuántas equivalen a una CX?",
                [
                    "las 40",
                    "unas 20, la mitad",
                    "solo las que eligen la identidad antes",
                    "ninguna: son circuitos distintos",
                ],
                "Anotado. Construyámoslas y comparemos matrices.",
            ),
        ),
        beat(
            "tw_codigo",
            ("", "Cuarenta variantes, una sola operación"),
            """Cada variante es un circuito de dos qubits. [[antes]]Elegimos la Pauli de antes con un generador aleatorio con semilla. [[despues]]Pauli punto evolve con la CNOT calcula la Pauli que hay que poner después.
             [[res]]Las cuarenta variantes equivalen a la CNOT, y usan quince Paulis distintas antes de ella. Si dijiste «ninguna», acabas de ver la clave: los circuitos son distintos, pero la operación es la misma. Lo que cambia es cómo se reparte el ruido de la puerta.""",
            [
                Code(
                    """import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import CXGate
from qiskit.quantum_info import Operator, Pauli

rng = np.random.default_rng(3)

def variante():
    antes = Pauli("".join(rng.choice(list("IXYZ"), 2)))
    despues = antes.evolve(CXGate())
    qc = QuantumCircuit(2)
    qc.append(antes.to_instruction(), [0, 1])
    qc.cx(0, 1)
    qc.append(despues.to_instruction(), [0, 1])
    return antes.to_label(), qc

variantes = [variante() for _ in range(40)]
iguales = sum(Operator(qc).equiv(Operator(CXGate())) for _, qc in variantes)
print("equivalentes a una CX:", iguales, "de 40")
print("Paulis distintas antes:", len({etiqueta for etiqueta, _ in variantes}))""",
                    id="c",
                    size=19,
                ),
                Out(
                    "equivalentes a una CX: 40 de 40\nPaulis distintas antes: 15",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="antes", lines=[9]),
                A("hl", "c", at="despues", lines=[10]),
                A("show", "o", at="res"),
                A("hl", "c", at="res", range="18-20"),
            ],
        ),
        beat(
            "activar",
            ("", "Activar las opciones"),
            """Las primitivas del lado del cliente exponen las dos opciones. [[dd]]En Sampler o Estimator puedes activar el desacoplamiento y elegir su secuencia.
             [[tw]]También puedes pedir twirling de puertas con `enable_gates`. [[aclaracion]]El siguiente bloque necesita un backend de IBM y credenciales, así que no lo ejecutamos durante la verificación local.""",
            [
                Code(
                    """from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime.executor_estimator import Estimator

backend = QiskitRuntimeService().least_busy(
    operational=True, simulator=False
)
estimator = Estimator(backend)
estimator.options.dynamical_decoupling.enable = True
estimator.options.dynamical_decoupling.sequence_type = "XpXm"
estimator.options.twirling.enable_gates = True""",
                    id="c",
                    norun=True,
                    size=20,
                )
            ],
            [A("hl", "c", at="dd", range="7-8"), A("hl", "c", at="tw", range="9-9")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Sobre el desacoplamiento dinámico.""",
            [
                T(
                    "Tu circuito tiene huecos largos en los que varios qubits quedan inactivos.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué técnica probarías primero?",
                ["aumentar la profundidad de optimización", "desacoplamiento dinámico", "ZNE"],
                1,
                "Correcto: el desacoplamiento dinámico está pensado para proteger qubits durante esperas.",
                wrong=[
                    "La transpilación puede ayudar, pero no llena las esperas con pulsos DD.",
                    None,
                    "ZNE extrapola expectativas medidas a varios niveles de ruido.",
                ],
            ),
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Una pregunta sobre twirling.""",
            [M(r"P_L\,G\,P_R = G", size=42)],
            ask=choice(
                "¿Qué cambia principalmente al promediar los circuitos twirleados?",
                ["el objetivo ideal", "el número de qubits", "la estructura del canal de ruido"],
                2,
                "Correcto: las variantes conservan la operación ideal y adaptan la estructura del ruido.",
                wrong=[
                    "El par de Paulis se elige para mantener el efecto ideal.",
                    "Twirling no cambia el ancho del circuito.",
                    None,
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. Abre el cuaderno de práctica con el comando de abajo. [[n1]]Primero rellenas los huecos de un circuito con la secuencia XX y compruebas que la operación no cambia. [[n2]]Después la alargas a cuatro pulsos X y cuentas el doble. [[n3]]Y por último escribes tú una variante de twirling de la CNOT: la Pauli de después que mantiene la operación.
             [[check]]Cada misión tiene una comprobación: busca la marca verde.""",
            [
                Mission(
                    "practica/p6-supresion.py",
                    [
                        (1, "Rellena los huecos con XX y verifica que la operación es la misma."),
                        (2, "Cambia la secuencia a cuatro pulsos X: debe añadir el doble."),
                        (
                            3,
                            "Escribe `variante(rng)`: elige `antes` al azar y calcula `despues` con `evolve`.",
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
            """Dos preguntas para pensar con calma. Ninguna tiene respuesta automática.""",
            [T("Lo que no cambia el resultado ideal puede cambiar el medido.", "subtitle")],
            ask=reflect(
                "Las dos técnicas añaden operaciones que, en el caso ideal, no hacen nada. ¿Por qué entonces pueden cambiar el resultado que mides en un QPU?",
                "¿En qué circuito de tu proyecto Ising crees que el desacoplamiento dinámico empeoraría las cosas? ¿Cómo lo comprobarías?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]El desacoplamiento dinámico inserta secuencias de pulsos en intervalos inactivos.
             [[r2]]Ayuda sobre todo cuando hay esperas; en un circuito denso puede no ayudar.
             [[r3]]El twirling usa pares de Paulis para conservar la operación ideal y aleatorizar cómo se presenta el ruido.
             [[r4]]Ambas opciones añaden recursos: compara su efecto en tu circuito.""",
            s_supresion,
            a_supresion,
        ),
    ],
    sources=[],
    practice=[
        "Revisa las opciones de [Estimator](https://quantum.cloud.ibm.com/docs/en/guides/estimator-noise-management) y [Sampler](https://quantum.cloud.ibm.com/docs/en/guides/sampler-noise-management) para el backend que planeas usar."
    ],
)


# ------------------------------------------------------------------ 6.3 Mitigación
s_mitigacion, a_mitigacion = resumen(
    [
        "TREX reduce sesgo de lectura; ZNE extrapola a factor cero",
        "PEA aprende el ruido antes de amplificarlo; PEC usa una mezcla cuasi-probabilística",
        "PEC puede ser no sesgada, con un costo que crece rápido con la profundidad",
        "PNA es una técnica de addons que absorbe ruido aprendido en el observable",
    ]
)
mitigacion = lesson(
    "p6-mitigacion",
    "Mitigación: TREX, ZNE, PEA, PEC y PNA",
    "Qué corrigen TREX, ZNE, PEA y PEC en IBM Quantum Compute, y dónde encaja PNA en el ecosistema de addons.",
    [
        "explicar la idea detrás de TREX y ZNE",
        "comparar PEA con PEC y su costo",
        "distinguir las opciones del servicio de una técnica de addon como PNA",
    ],
    [
        beat(
            "intro",
            ("", "Estimar el resultado sin ruido"),
            """La mitigación no quita el ruido del dispositivo. [[idea]]Ejecuta circuitos relacionados y combina sus resultados para estimar una expectativa más cercana al valor ideal.
             [[expectativas]]Estas herramientas del servicio se enfocan en expectativas de observables, como la energía de un estado. Para corregir una distribución de muestras completa se necesitan otros métodos y otro criterio de calidad.""",
            [
                Flow(
                    [
                        dict(t="circuitos relacionados"),
                        dict(t="más disparos", color="gold"),
                        dict(t="estimación corregida", color="blue"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="idea", i=0),
                A("item", "f", at="idea", i=1),
                A("item", "f", at="expectativas", i=2),
            ],
        ),
        beat(
            "trex",
            ("", "TREX corrige sesgo de lectura"),
            """TREX significa extinción del error de lectura con twirling. [[medicion]]Para estimar una expectativa de Pauli, intercala una aleatorización de la medición que diagonaliza el error de lectura.
             [[calibracion]]El servicio aprende factores de escala con circuitos de calibración y los usa para reducir el sesgo. [[costo]]Hay una ejecución adicional de calibración: la mitigación mejora el estimador si el modelo sigue describiendo bien al dispositivo, pero consume tiempo y disparos.""",
            [
                Box(
                    "def",
                    "TREX",
                    T("reduce sesgo de lectura en expectativas de observables Pauli", "body"),
                    id="b",
                ),
                T(
                    "Mediciones de calibración → factores de escala → expectativa corregida",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [A("show", "b", at="medicion"), A("show", "n", at="calibracion")],
        ),
        beat(
            "zne",
            ("", "ZNE extrapola hacia ruido cero"),
            """La extrapolación a ruido cero ejecuta el circuito con varios niveles de ruido. [[amplificar]]En el servicio, una forma de amplificarlo es el plegado digital: reemplazar una puerta de dos qubits U por la secuencia U, U daga, U, que tiene la misma operación ideal y más puertas físicas.
             [[factores]]Se miden expectativas en factores de ruido, por ejemplo uno, tres y cinco. [[extrapolar]]Luego se ajusta una curva y se estima dónde estaría el resultado al extrapolar al factor cero.
             [[noexacta]]Esa curva depende de pocos puntos ruidosos: el ajuste puede ser sesgado y no garantiza recuperar el valor exacto.""",
            [
                Flow(
                    [
                        dict(t="factor 1", s="circuito original"),
                        dict(t="factor 3", s="puertas plegadas"),
                        dict(t="factor 5", s="más ruido"),
                        dict(t="factor 0", s="extrapolación", color="blue"),
                    ],
                    id="f",
                    stagger=True,
                ),
                Box(
                    "warn",
                    "No es una garantía",
                    T("un resultado extrapolado también tiene incertidumbre", "body"),
                    id="b",
                    hidden=True,
                ),
            ],
            [
                A("item", "f", at="amplificar", i=0),
                A("item", "f", at="factores", i=1),
                A("item", "f", at="factores", t=1.5, i=2),
                A("item", "f", at="extrapolar", i=3),
                A("show", "b", at="noexacta"),
            ],
        ),
        beat(
            "predice_zne",
            ("", "Antes de extrapolar"),
            """Un caso concreto. [[ghz]]Un estado GHZ de cuatro qubits, con un dos por ciento de error despolarizante en cada CNOT, y el observable Z cero por Z tres, cuyo valor ideal es uno. [[tabla]]Medimos con los factores de ruido uno, tres y cinco, y el valor baja: cero coma nueve cuatro, cero coma ocho tres, cero coma siete tres.
             [[apuesta]]Ajusta una recta por esos tres puntos y llévala al factor cero. Apuesta: ¿a qué valor llega?""",
            [
                Table(
                    ["Factor de ruido", "⟨Z₀Z₃⟩ medido"],
                    [["1", "0.9412"], ["3", "0.8337"], ["5", "0.7386"], ["0", "?"]],
                    id="t",
                    stagger=True,
                    size=24,
                )
            ],
            [
                A("item", "t", at="tabla", i=0),
                A("item", "t", at="tabla", t=0.8, i=1),
                A("item", "t", at="tabla", t=1.6, i=2),
                A("item", "t", at="apuesta", i=3),
            ],
            ask=predict(
                "La recta que pasa por esos puntos, ¿qué valor da en el factor 0?",
                [
                    "exactamente 1.0000",
                    "cerca de 0.99, se queda corta",
                    "más de 1.05, se pasa",
                    "0.94, igual que sin extrapolar",
                ],
                "Anotado. Hagamos el ajuste.",
            ),
        ),
        beat(
            "zne_ajuste",
            ("", "Recta frente a exponencial"),
            """Dos ajustes con numpy. [[recta]]Una recta con polyfit de grado uno; el término independiente es el valor en cero. Da cero coma nueve ocho nueve ocho: mejor que el cero coma nueve cuatro sin mitigar, pero se queda corta.
             [[exp]]Con ruido despolarizante cada puerta multiplica el valor por un factor fijo, así que los puntos siguen una exponencial. Una exponencial es una recta en el logaritmo: ajustamos log de los valores y deshacemos el logaritmo.
             [[res]]Sale uno coma cero cero cero cero. Es exacto porque este ruido es exactamente despolarizante; en un QPU real la curva es solo una aproximación, y por eso conviene elegir el modelo de extrapolación con cuidado.""",
            [
                Code(
                    """import numpy as np

factores = [1, 3, 5]
valores = [0.9412, 0.8337, 0.7386]

recta = np.polyfit(factores, valores, 1)[1]
exponencial = np.exp(np.polyfit(factores, np.log(valores), 1)[1])
print(f"recta: {recta:.4f}")
print(f"exponencial: {exponencial:.4f}")""",
                    id="c",
                    size=23,
                ),
                Out("recta: 0.9898\nexponencial: 1.0000", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="recta", lines=[6]),
                A("hl", "c", at="exp", lines=[7]),
                A("show", "o", at="res"),
            ],
        ),
        beat(
            "pea",
            ("", "PEA aprende antes de amplificar"),
            """PEA mejora la etapa de amplificación de ZNE. [[aprender]]Primero aprende un modelo de ruido twirleado para las capas de puertas de dos qubits del circuito.
             [[inyectar]]Después aumenta el ruido de forma probabilística, usando ese modelo, en vez de confiar solo en plegar puertas. [[extrapolar]]Por último, extrapola las expectativas a ruido cero como ZNE.
             [[nota]]En el Estimator nuevo del lado del cliente, el aprendizaje explícito del ruido es un trabajo separado; en la primitiva antigua el servicio podía gestionarlo internamente.""",
            [
                Flow(
                    [
                        dict(t="aprender capas", color="blue"),
                        dict(t="amplificar según el modelo"),
                        dict(t="extrapolar", color="gold"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="aprender", i=0),
                A("item", "f", at="inyectar", i=1),
                A("item", "f", at="extrapolar", i=2),
            ],
        ),
        beat(
            "pec",
            ("", "PEC cancela sesgo con más costo"),
            """La cancelación probabilística de errores expresa la operación ideal como una combinación de circuitos ruidosos que sí se pueden ejecutar. [[muestreo]]El servicio sortea esos circuitos con pesos positivos y negativos y combina sus resultados.
             [[sin_sesgo]]En promedio, la estimación puede ser no sesgada. [[varianza]]Pero el costo de muestreo crece rápidamente con el tamaño de esos pesos; para circuitos profundos puede volverse prohibitivo.
             [[modelo]]Por eso PEC necesita un modelo de ruido de las capas, y limitar el overhead puede dejar más incertidumbre de la que pediste.""",
            [
                Row(
                    Box("def", "Ventaja", T("estimación no sesgada en promedio", "body"), id="a"),
                    Box(
                        "warn",
                        "Costo",
                        T("más variantes y disparos; crece con la profundidad", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=20,
                )
            ],
            [A("show", "a", at="sin_sesgo"), A("show", "b", at="varianza")],
        ),
        beat(
            "pna",
            ("", "PNA vive en los addons"),
            """El panorama oficial también incluye PNA, absorción de ruido propagado. [[diferencia]]Es una técnica de addons: aprende canales de ruido y absorbe sus inversas en el observable mediante propagación de Paulis.
             [[lugar]]No es un interruptor del mismo tipo que TREX o ZNE en la tabla de resiliencia del servicio. Se usa en flujos más personalizables junto al modelo de ejecución dirigida.
             [[decidir]]La idea para elegir es gradual: primero prueba las opciones administradas; pasa a un flujo de addon cuando necesitas controlar explícitamente cómo se aprende o se propaga el ruido.""",
            [
                Table(
                    ["En el servicio", "En el ecosistema de addons"],
                    [
                        ["TREX, ZNE, PEA y PEC", "PNA y flujos personalizados"],
                        ["opciones de Estimator", "control explícito de datos y pasos"],
                    ],
                    id="t",
                    stagger=True,
                    size=23,
                )
            ],
            [A("item", "t", at="diferencia", i=0), A("item", "t", at="lugar", i=1)],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Una pregunta sobre el sesgo.""",
            [
                T(
                    "Quieres una estimación que sea no sesgada en promedio, aunque necesite muchos más disparos.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué técnica corresponde a esa descripción?",
                ["TREX", "PEC", "twirling de puertas"],
                1,
                "Correcto: PEC busca una estimación no sesgada, con un overhead de muestreo que puede ser grande.",
                wrong=[
                    "TREX se enfoca en el sesgo de lectura.",
                    None,
                    "Twirling modifica la estructura del ruido; no es PEC.",
                ],
            ),
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Sobre la extrapolación a ruido cero.""",
            [
                Flow(
                    [
                        dict(t="ruido real"),
                        dict(t="factor 1"),
                        dict(t="factor 3"),
                        dict(t="factor 0"),
                    ],
                    id="f",
                )
            ],
            ask=choice(
                "¿El factor cero se mide directamente en el QPU?",
                ["sí, con más disparos", "no: se estima a partir de puntos ruidosos"],
                1,
                "Correcto: el hardware siempre tiene ruido; ZNE extrapola desde resultados medidos a varios factores.",
                wrong=["No existe una ejecución física sin ruido.", None],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. Abre el cuaderno de práctica con el comando de abajo. [[n1]]Primero haces ZNE con una recta sobre el GHZ y ves cuánto se queda corta. [[n2]]Después cambias a una exponencial y llegas al valor ideal. [[n3]]Y por último escribes los pesos de PEC para un qubit, con un peso negativo, y calculas cuánto crece el número de disparos.
             [[check]]Cada misión tiene una comprobación: busca la marca verde.""",
            [
                Mission(
                    "practica/p6-mitigacion.py",
                    [
                        (1, "Mide a factores 1, 3 y 5 y extrapola con una recta."),
                        (2, "Ajusta una exponencial: el error debe bajar de $10^{-3}$."),
                        (
                            3,
                            "Escribe `pesos_pec(lam)` y mira cómo crece el sobrecoste $\\gamma^{2n}$ con la profundidad.",
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
            """Dos preguntas para pensar con calma, conectadas con tu proyecto.""",
            [T("Una extrapolación es un modelo, no una medida.", "subtitle")],
            ask=reflect(
                "La exponencial dio exactamente 1 en el cuaderno. ¿Por qué eso no te garantiza nada en un QPU real?",
                "PEC no tiene sesgo pero su costo crece muy rápido con la profundidad; ZNE es barato pero sesgado. Para tu cadena de Ising con muchos pasos de Trotter, ¿cuál probarías primero?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]TREX reduce sesgo de lectura; ZNE extrapola expectativas al factor cero.
             [[r2]]PEA aprende el ruido para amplificarlo mejor; PEC puede ser no sesgada, pero cuesta muchos disparos.
             [[r3]]PNA absorbe ruido aprendido en el observable mediante propagación de Paulis y pertenece a flujos de addons.
             [[r4]]La mitigación ayuda a estimar expectativas, pero su beneficio y su costo dependen del circuito.""",
            s_mitigacion,
            a_mitigacion,
        ),
    ],
    sources=["error-mitigation-and-suppression-techniques"],
    practice=[
        "Compara el costo de factores de ruido `[1, 3, 5]` con el de un solo circuito y decide qué overhead tolera tu problema."
    ],
)


# ------------------------------------------------------------------ 6.4 Configurar el ruido
s_configurar, a_configurar = resumen(
    [
        "resilience_level 0: sin mitigación; 1 (por defecto): TREX; 2: TREX + ZNE y twirling",
        "Sampler ofrece supresión; Estimator también ofrece mitigación de expectativas",
        "las opciones explícitas se combinan con el nivel y pueden prevalecer sobre su valor base",
        "la disponibilidad y el costo dependen del tipo de circuito",
    ]
)
configurar = lesson(
    "p6-configurar",
    "Configurar el ruido en Estimator y Sampler",
    "Ajustar niveles de resiliencia y opciones de supresión en las primitivas nuevas del lado del cliente.",
    [
        "interpretar los niveles de resiliencia de Estimator",
        "configurar opciones individuales sin confundirlas con un nivel",
        "reconocer que Sampler y Estimator ofrecen herramientas distintas",
    ],
    [
        beat(
            "intro",
            ("", "Un nivel no es una promesa"),
            """Las opciones permiten elegir un intercambio entre costo y reducción de sesgo. [[resilience]]En Estimator, `resilience_level` resume un paquete de técnicas. [[beta]]Estos niveles siguen en beta: el overhead y la calidad varían por circuito, y no se garantiza que cada técnica se aplique en todos los casos.
             [[detalle]]Si necesitas controlar una técnica concreta, usa sus opciones individuales y consulta la tabla de compatibilidad del tipo de circuito.""",
            [
                Box(
                    "warn",
                    "Beta",
                    T("el nivel describe una estrategia, no garantiza una mejora exacta", "body"),
                    id="b",
                ),
                T(
                    "Primero define la salida que te importa: una expectativa o una distribución de muestras.",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [A("show", "b", at="beta"), A("show", "n", at="detalle")],
        ),
        beat(
            "predice_nivel",
            ("", "¿Y si no pides ningún nivel?"),
            """Antes de ver la tabla de niveles, una apuesta. [[crear]]Creas un Estimator y no tocas ninguna opción. [[apuesta]]¿Qué valor de resilience level tendrá? Cero significa sin mitigación; uno, TREX; dos, TREX más extrapolación a ruido cero.""",
            [Code("estimator = Estimator(backend)   # sin opciones", id="c", norun=True, size=26)],
            [A("hl", "c", at="crear", lines=[1])],
            ask=predict(
                "¿Qué `resilience_level` tendrá ese Estimator?",
                ["0, sin mitigación", "1, TREX", "2, TREX + ZNE + twirling"],
                "Anotado. Lo leemos del propio objeto de opciones.",
            ),
        ),
        beat(
            "niveles",
            ("", "Los niveles de Estimator"),
            """En la tabla documentada, nivel cero desactiva la mitigación. [[cero]]Nivel uno aplica TREX para reducir errores de lectura. [[uno]]Nivel dos añade extrapolación a ruido cero y twirling de puertas.
             [[defecto]]Y la respuesta a la apuesta: el nivel uno es el valor por defecto. Un Estimator sin opciones ya mitiga el error de lectura. Las opciones se validan en local, sin cuenta: con un backend falso puedes leerlas.
             [[costo]]El nivel dos suele consumir más muestreo que el uno. El nombre ‘resilience’ no significa que el resultado sea inmune al ruido.""",
            [
                Table(
                    ["Nivel", "Método"],
                    [
                        ["0", "sin mitigación"],
                        ["1", "TREX · mitigación de lectura (por defecto)"],
                        ["2", "TREX + ZNE + twirling de puertas"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                ),
                Code(
                    "print(Estimator(backend).options.resilience_level)",
                    id="d",
                    hidden=True,
                    size=24,
                    setup="from qiskit_ibm_runtime.executor_estimator import Estimator\nfrom qiskit_ibm_runtime.fake_provider import FakeManilaV2\nbackend = FakeManilaV2()",
                ),
                Out("1", id="o", hidden=True, check=True),
            ],
            [
                A("item", "t", at="cero", i=0),
                A("item", "t", at="uno", i=1),
                A("show", "d", at="defecto"),
                A("show", "o", at="defecto"),
                A("item", "t", at="costo", i=2),
            ],
        ),
        beat(
            "estimator",
            ("", "Elegir un nivel"),
            """El código usa el Estimator nuevo del lado del cliente, incluido en `qiskit-ibm-runtime` cero punto cincuenta o posterior. [[importar]]Se importa desde `executor_estimator`, se conecta al backend y recibe `resilience_level` en sus opciones.
             [[auth]]Necesitas credenciales y un backend real para enviar este trabajo; la verificación local del curso no lo ejecuta.""",
            [
                Code(
                    """from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime.executor_estimator import Estimator

backend = QiskitRuntimeService().least_busy(
    operational=True, simulator=False
)
estimator = Estimator(backend, options={"resilience_level": 2})
job = estimator.run(pubs)
result = job.result()""",
                    id="c",
                    norun=True,
                    size=21,
                )
            ],
            [
                A("hl", "c", at="importar", range="1-2"),
                A("hl", "c", at="importar", range="7-7"),
                A("hl", "c", at="auth", range="4-6"),
            ],
        ),
        beat(
            "custom",
            ("", "Ajustes individuales"),
            """Puedes activar una opción específica sin depender solo del nivel. [[medir]]Por ejemplo, TREX se configura con `measure_mitigation`; ZNE, con `zne_mitigation`.
             [[combinar]]Las opciones que escribes se agregan al paquete base del nivel y pueden reemplazar sus valores. [[compat]]No todas las combinaciones son compatibles con todos los circuitos, así que la tabla de compatibilidad es parte de la configuración, no una nota al pie.""",
            [
                Code(
                    """estimator = Estimator(backend)
estimator.options.resilience.measure_mitigation = True
estimator.options.resilience.zne_mitigation = True
estimator.options.resilience.zne.noise_factors = (1, 3, 5)""",
                    id="c",
                    size=22,
                    setup="from qiskit_ibm_runtime.executor_estimator import Estimator\nfrom qiskit_ibm_runtime.fake_provider import FakeManilaV2\nbackend = FakeManilaV2()",
                ),
                Box(
                    "idea",
                    "Revisa compatibilidad",
                    T(
                        "las técnicas disponibles dependen de las puertas y mediciones del circuito",
                        "body",
                    ),
                    id="b",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="medir", range="2-2"),
                A("hl", "c", at="medir", range="3-4"),
                A("show", "b", at="compat"),
            ],
        ),
        beat(
            "sampler",
            ("", "Sampler prioriza supresión"),
            """Sampler devuelve muestras, así que sus opciones de gestión del ruido son distintas. [[tiene]]La documentación presenta desacoplamiento dinámico y twirling de puertas para Sampler. [[no_trex]]TREX y ZNE se aplican a expectativas de Estimator; no elijas un nivel de Estimator para corregir una distribución de Sampler.
             [[code]]El ejemplo activa una secuencia de desacoplamiento y el twirling. Las opciones se escriben igual con un backend real o con uno falso; solo el backend real exige credenciales.""",
            [
                Code(
                    """from qiskit_ibm_runtime.executor_sampler import Sampler

sampler = Sampler(backend)
sampler.options.dynamical_decoupling.enable = True
sampler.options.dynamical_decoupling.sequence_type = "XpXm"
sampler.options.twirling.enable_gates = True""",
                    id="c",
                    size=22,
                    setup="from qiskit_ibm_runtime.fake_provider import FakeManilaV2\nbackend = FakeManilaV2()",
                ),
                Table(
                    ["Sampler", "Estimator"],
                    [
                        ["DD + twirling de puertas", "DD + twirling + mitigación de expectativas"],
                    ],
                    id="t",
                    hidden=True,
                    size=22,
                ),
            ],
            [A("hl", "c", at="tiene", range="3-5"), A("show", "t", at="no_trex")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Sobre las opciones de Sampler.""",
            [
                T(
                    "Quieres reducir el sesgo de lectura de una expectativa Z medida con Estimator.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué configuración usarías?",
                ["Sampler con `resilience_level=2`", "Estimator con TREX", "Sampler con ZNE"],
                1,
                "Correcto: TREX mitiga error de lectura al estimar expectativas con Estimator.",
                wrong=[
                    "Sampler no usa los niveles de resiliencia de Estimator.",
                    None,
                    "ZNE es una técnica de expectativas de Estimator, no de Sampler.",
                ],
            ),
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Sobre niveles y opciones explícitas.""",
            [T("Configuras un nivel base y, además, activas una opción individual.", "body")],
            ask=choice(
                "¿La opción individual puede cambiar el valor base del nivel?",
                [
                    "no, siempre se ignora",
                    "sí, las opciones explícitas se aplican además del nivel",
                    "solo si el nivel es cero",
                ],
                1,
                "Correcto: las opciones explícitas se aplican además de la configuración base del nivel.",
                wrong=["No se ignoran.", None, "Pueden combinarse con cualquier nivel compatible."],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. Abre el cuaderno de práctica con el comando de abajo. Las opciones se validan en local, así que no hace falta cuenta. [[n1]]Primero lees lo que trae por defecto un Estimator y un Sampler. [[n2]]Después partes del nivel cero y activas TREX y ZNE a mano, y pruebas un nivel inválido para ver el error. [[n3]]Y por último escribes una función que prepara cualquiera de las dos primitivas y rechaza TREX o ZNE para el Sampler.
             [[check]]Cada misión tiene una comprobación: busca la marca verde.""",
            [
                Mission(
                    "practica/p6-configurar.py",
                    [
                        (
                            1,
                            "Crea un Estimator y un Sampler sin opciones y lee sus valores por defecto.",
                        ),
                        (
                            2,
                            "Nivel 0 más TREX y ZNE con factores 1, 3 y 5; prueba `resilience_level = 7`.",
                        ),
                        (
                            3,
                            'Escribe `preparar(primitiva, tecnicas)`: un Sampler con `"trex"` o `"zne"` lanza `ValueError`.',
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
            """Dos preguntas para pensar con calma.""",
            [T("Un nivel resume una estrategia; no la garantiza.", "subtitle")],
            ask=reflect(
                "El nivel por defecto ya aplica TREX sin que lo pidas. ¿Qué ventaja y qué riesgo tiene que una mitigación esté activada por defecto?",
                "Para tu cadena de Ising, ¿empezarías con el nivel 1, con el 2 o con opciones individuales? ¿Qué medirías para decidir?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Estimator ofrece niveles cero, uno y dos; el uno es el de por defecto, y el dos añade ZNE y twirling.
             [[r2]]Puedes fijar técnicas individuales, respetando las compatibilidades.
             [[r3]]Sampler se centra en desacoplamiento dinámico y twirling; no ofrece la mitigación de expectativas de Estimator.
             [[r4]]Los niveles están en beta: compara calidad, overhead y circuito real.""",
            s_configurar,
            a_configurar,
        ),
    ],
    sources=["estimator-noise-management", "sampler-noise-management"],
    practice=[
        "En un circuito pequeño, prueba primero el nivel cero y luego TREX; registra expectativa, número de disparos y tiempo de ejecución."
    ],
)


# ------------------------------------------------------------------ 6.5 Aprender el ruido
s_aprender, a_aprender = resumen(
    [
        "NoiseLearner estima un modelo Pauli–Lindblad por capas entrelazadoras",
        "NoiseLearnerV3 acepta cajas anotadas y deja elegir cómo agrupar capas",
        "con el Estimator nuevo, aprender el ruido es un trabajo separado",
        "el modelo caracteriza el ruido; PEC o PEA lo usan para mitigar",
    ]
)
aprender_ruido = lesson(
    "p6-aprender-ruido",
    "Aprender el ruido",
    "Caracterizar el ruido por capas con NoiseLearner y NoiseLearnerV3 para alimentar técnicas de mitigación.",
    [
        "describir qué es un modelo Pauli–Lindblad",
        "distinguir las entradas de NoiseLearner y NoiseLearnerV3",
        "conectar el modelo aprendido con PEA o PEC",
    ],
    [
        beat(
            "intro",
            ("", "Medir el ruido que afecta a tus capas"),
            """Para usar PEA o PEC no basta con saber que existe ruido; hace falta estimar cómo afecta a las puertas del circuito. [[modelo]]El NoiseLearner ejecuta experimentos de caracterización y ajusta un modelo de ruido Pauli–Lindblad para las capas relevantes.
             [[no_corrige]]Aprender el modelo no corrige el resultado por sí solo. Es una medición auxiliar que otra técnica, como PEA o PEC, usa después.""",
            [
                Row(
                    Box("idea", "NoiseLearner", T("caracteriza", "body"), id="a"),
                    Box("def", "PEA / PEC", T("usan el modelo", "body"), id="b", hidden=True),
                    gap=22,
                )
            ],
            [A("show", "a", at="modelo"), A("show", "b", at="no_corrige")],
        ),
        beat(
            "modelo",
            ("", "Un canal para cada capa"),
            """El modelo Pauli–Lindblad describe errores con generadores de Pauli y sus tasas. [[capas]]Se aprende por capas de puertas de dos qubits que el circuito realmente ejecutará, después de transpilarlo al conjunto de instrucciones del dispositivo.
             [[tasas]]Una tasa mayor indica que ese término pesa más en el modelo ajustado. Es una descripción aproximada del ruido en una calibración; no mide cada posible efecto físico ni permanece fija para siempre.""",
            [
                M(
                    r"\Lambda(\rho)=\exp\!\left(\sum_j r_j(P_j\rho P_j-\rho)\right)",
                    size=34,
                    id="eq",
                ),
                Table(
                    ["Símbolo", "Significado"],
                    [
                        ["`Pⱼ`", "generador de Pauli"],
                        ["`rⱼ`", "tasa aprendida"],
                        ["`Λ`", "canal aproximado para la capa"],
                    ],
                    id="t",
                    hidden=True,
                    stagger=True,
                    size=23,
                ),
            ],
            [A("show", "eq", at="capas"), A("show", "t", at="tasas")],
        ),
        beat(
            "predice_decae",
            ("", "Antes de medir la capa"),
            """¿Cómo se aprende una tasa? Repitiendo la capa y mirando cómo decae un valor esperado. [[capa]]Aquí la capa son dos CNOT seguidas, que sin ruido serían la identidad, con un tres por ciento de error despolarizante en cada una. [[medida]]Partimos de cero cero y medimos Z por Z tras una, dos, cuatro y ocho capas.
             [[apuesta]]Apuesta: ¿cómo baja el valor al repetir la capa?""",
            [
                Flow(
                    [
                        dict(t="|00⟩"),
                        dict(t="capa × d", s="2 CX con ruido", color="gold"),
                        dict(t="⟨ZZ⟩", s="d = 1, 2, 4, 8", color="blue"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [A("item", "f", at="capa", i=1), A("item", "f", at="medida", i=2)],
            ask=predict(
                "Al duplicar el número de capas, ⟨ZZ⟩…",
                [
                    "baja la misma cantidad cada capa (una recta)",
                    "se multiplica por el mismo factor cada capa (una exponencial)",
                    "casi no cambia",
                    "oscila hacia arriba y abajo",
                ],
                "Anotado. Calculémoslo con una simulación exacta.",
            ),
        ),
        beat(
            "decae",
            ("", "Cada capa multiplica por lo mismo"),
            """El cálculo. [[canal]]Un canal despolarizante de dos qubits, convertido a canal cuántico, y una CNOT. [[bucle]]Cada capa aplica dos veces la CNOT y el canal sobre una matriz de densidad que parte de cero cero. [[obs]]Y al final se lee el valor esperado de Z por Z.
             [[res]]Los valores bajan de cero coma nueve cuatro a cero coma seis uno en ocho capas. El cociente entre capas consecutivas es constante: cero coma nueve cuatro cero nueve, que es uno menos cero coma cero tres, al cuadrado. Es una exponencial, y ese factor es la fidelidad de Pauli de la capa.
             [[ajuste]]Por eso se ajusta una recta al logaritmo: la pendiente da la fidelidad, y de la fidelidad sale la tasa del modelo Pauli–Lindblad.""",
            [
                Code(
                    """from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix, SparsePauliOp
from qiskit_aer.noise import depolarizing_error

canal = depolarizing_error(0.03, 2).to_quantumchannel()
cx = QuantumCircuit(2)
cx.cx(0, 1)

def zz_tras(d):
    rho = DensityMatrix.from_label("00")
    for _ in range(2 * d):
        rho = rho.evolve(cx).evolve(canal)
    return float(rho.expectation_value(SparsePauliOp("ZZ")).real)

for d in (1, 2, 4, 8):
    print(d, round(zz_tras(d), 4))
print("cociente 2 capas / 1 capa:", round(zz_tras(2) / zz_tras(1), 4))""",
                    id="c",
                    size=18,
                ),
                Out(
                    "1 0.9409\n2 0.8853\n4 0.7837\n8 0.6143\ncociente 2 capas / 1 capa: 0.9409",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="canal", range="5-7"),
                A("hl", "c", at="bucle", range="10-12"),
                A("hl", "c", at="obs", lines=[13]),
                A("show", "o", at="res"),
                A("hl", "c", at="ajuste", range="15-17"),
            ],
        ),
        beat(
            "versiones",
            ("", "De NoiseLearner a NoiseLearnerV3"),
            """La versión anterior, NoiseLearner, recibe circuitos o PUBs y aplica su propia forma de encontrar capas. [[nuevo]]NoiseLearnerV3 recibe cajas anotadas que ya representan instrucciones ISA y permite que tú decidas qué capas caracterizar.
             [[estimador]]Con el Estimator nuevo del lado del cliente, puedes obtener esas capas con `find_unique_layers`. [[ejecutor]]Con Executor, se generan cajas con Samplomatic y se buscan instrucciones únicas.
             [[migrar]]La versión V3 es la opción para el modelo de ejecución dirigida y las primitivas del lado del cliente; no mezcles los dos formatos de entrada.""",
            [
                Table(
                    ["Clase", "Entrada"],
                    [
                        ["`NoiseLearner`", "circuitos o PUBs"],
                        ["`NoiseLearnerV3`", "cajas twirleadas con puertas ISA"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                ),
                T("Estimator: `find_unique_layers(pubs)`", "note", id="n", hidden=True),
                T("Executor: cajas con anotaciones de Samplomatic", "note", id="x", hidden=True),
            ],
            [
                A("item", "t", at="versiones", i=0),
                A("item", "t", at="nuevo", i=1),
                A("show", "n", at="estimador"),
                A("show", "x", at="ejecutor"),
            ],
        ),
        beat(
            "flujo",
            ("", "El flujo con Estimator"),
            """Con client-side Estimator, primero transpila y prepara el PUB. [[capas]]Después `find_unique_layers` extrae las capas anotadas que necesita aprender.
             [[job]]NoiseLearnerV3 ejecuta un trabajo separado de aprendizaje. [[resultado]]Al recibir los mapas Pauli–Lindblad, los asocias con esas capas en `layer_noise_model`; luego ejecutas la mitigación.
             [[credenciales]]Este ejemplo envía trabajos a un backend real y requiere credenciales; lo omitimos en la verificación automática.""",
            [
                Code(
                    """from qiskit_ibm_runtime import NoiseLearnerV3
from qiskit_ibm_runtime.executor_estimator import Estimator

estimator = Estimator(backend)
estimator.options.resilience.pec_mitigation = True
layers = estimator.find_unique_layers(pubs)

learner_job = NoiseLearnerV3(backend).run(layers)
learner_result = learner_job.result()
maps = learner_result.to_pauli_lindblad_maps()
estimator.options.resilience.layer_noise_model = zip(layers, maps)
result = estimator.run(pubs).result()""",
                    id="c",
                    norun=True,
                    size=20,
                )
            ],
            [
                A("hl", "c", at="capas", range="5-5"),
                A("hl", "c", at="job", range="7-8"),
                A("hl", "c", at="resultado", range="9-10"),
            ],
        ),
        beat(
            "limites",
            ("", "Qué significa y qué no"),
            """El modelo aprende ruido de las instrucciones y capas que le entregaste. [[sirve]]Sirve para comparar opciones y alimentar una mitigación que usa ese modelo.
             [[no]]No es una copia perfecta del QPU ni una garantía sobre ejecuciones futuras. [[vigencia]]Si cambia el backend, el circuito o la calibración, el modelo puede dejar de describir la situación actual; vuelve a aprender cuando cambie lo que importa.""",
            [
                Row(
                    Box("def", "Sí", T("modelo por capas, útil para PEA y PEC", "body"), id="a"),
                    Box(
                        "warn",
                        "No",
                        T("predicción exacta para cualquier circuito y fecha", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=22,
                )
            ],
            [A("show", "a", at="sirve"), A("show", "b", at="no")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Sobre la entrada de NoiseLearnerV3.""",
            [
                T(
                    "Ya transpile tu circuito y quieres caracterizar capas para el Estimator nuevo.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué le pasas a `NoiseLearnerV3.run()`?",
                [
                    "el circuito abstracto antes de transpilar",
                    "una lista de cajas anotadas con instrucciones ISA",
                    "solo una cadena de Paulis",
                ],
                1,
                "Correcto: V3 trabaja con instrucciones BoxOp twirleadas y puertas del conjunto ISA.",
                wrong=[
                    "V3 necesita instrucciones ya preparadas.",
                    None,
                    "El resultado incluye cadenas de Pauli; no son la entrada.",
                ],
            ),
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """¿Qué hace el trabajo de NoiseLearner?""",
            [
                Flow(
                    [
                        dict(t="circuito"),
                        dict(t="medir ruido"),
                        dict(t="modelo"),
                        dict(t="mitigar"),
                    ],
                    id="f",
                )
            ],
            ask=choice(
                "¿El aprendizaje reduce el error directamente?",
                [
                    "sí, reemplaza las puertas",
                    "no, entrega un modelo para otra técnica",
                    "sí, filtra todas las muestras malas",
                ],
                1,
                "Correcto: el aprendizaje caracteriza el ruido; PEA o PEC usan el modelo para mitigar.",
                wrong=[
                    "No modifica el circuito objetivo.",
                    None,
                    "Ese es otro flujo de postselección.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. Abre el cuaderno de práctica con el comando de abajo. No necesita cuenta: el modelo de ruido es una lista de Paulis con tasas. [[n1]]Primero construyes un modelo Pauli–Lindblad y calculas cuánto cuesta invertirlo. [[n2]]Después lo amplificas multiplicando sus tasas por tres, como hace PEA. [[n3]]Y por último aprendes tú una fidelidad: mides cómo decae un valor esperado con la profundidad y ajustas la tasa.
             [[check]]Cada misión tiene una comprobación: busca la marca verde.""",
            [
                Mission(
                    "practica/p6-aprender-ruido.py",
                    [
                        (
                            1,
                            "Construye un `PauliLindbladMap` y calcula $\\gamma$ para invertir una capa.",
                        ),
                        (
                            2,
                            "Obtén el modelo amplificado con `scale_rates(3)` y comprueba que $\\gamma$ pasa a $\\gamma^3$.",
                        ),
                        (
                            3,
                            "Ajusta $f$ con $\\langle ZZ\\rangle(d)=f^d$ y calcula la tasa $r=-\\tfrac12\\ln f$.",
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
            """Dos preguntas para pensar con calma.""",
            [
                T(
                    "Un modelo aprendido describe una calibración, no el dispositivo para siempre.",
                    "subtitle",
                )
            ],
            ask=reflect(
                "En el cuaderno un solo término reprodujo la fidelidad de $ZZ$. ¿Qué otras medidas necesitarías para distinguir los muchos términos del ruido real de una capa?",
                "¿Cada cuánto crees que habría que volver a aprender el modelo si ejecutas tu cadena de Ising durante varios días? ¿Qué lo cambiaría?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]NoiseLearner ajusta un modelo Pauli–Lindblad por capas de puertas.
             [[r2]]NoiseLearnerV3 recibe cajas anotadas y se integra con Executor y el Estimator nuevo.
             [[r3]]En el cliente, el aprendizaje ocurre como un trabajo separado y se asigna a `layer_noise_model`.
             [[r4]]El modelo caracteriza; PEA o PEC realizan la mitigación.""",
            s_aprender,
            a_aprender,
        ),
    ],
    sources=["noise-learning", "migrate-to-noise-learner-v3"],
    practice=[
        "Transpila un circuito corto al backend y compara cuántas capas distintas encuentra `Estimator.find_unique_layers`."
    ],
)


# ------------------------------------------------------------------ 6.6 Postselección
s_post, a_post = resumen(
    [
        "medir · X lento (RX) · medir otra vez: el bit debe invertirse",
        "`AddSpectatorMeasures` + `AddPostSelectionMeasures` · también en qubits espectadores",
        "`PostSelector.compute_mask`: `True` conserva · `node` es estricta, `edge` permisiva",
        "cuesta disparos y no siempre mejora: compara con y sin filtrar",
    ]
)
postseleccion = lesson(
    "p6-postseleccion",
    "Postselección",
    "Añadir controles de error no Markoviano y filtrar muestras con verificaciones sobre qubits activos y espectadores.",
    [
        "explicar qué verifica un control de inversión de bit",
        "crear una máscara de postselección por nodo o por arista",
        "distinguir filtrado de corrección de errores",
    ],
    [
        beat(
            "intro",
            ("", "Filtrar muestras sospechosas"),
            """Postseleccionar significa conservar solo algunas muestras después de medir. [[no_postselect]]En esta lección no elegimos un resultado por tener una propiedad física deseada; buscamos señales de que el dispositivo pudo sufrir un error no Markoviano y descartamos las muestras que fallan esos controles.
             [[costo]]La técnica cambia la distribución observada y reduce el número de disparos útiles. Hay que reportar cuántas muestras sobreviven, no solo el resultado filtrado.""",
            [
                Box(
                    "warn",
                    "No es corrección",
                    T(
                        "filtrar no recupera el estado perdido y puede descartar muchas muestras",
                        "body",
                    ),
                    id="b",
                ),
                T(
                    "A cada disparo se le añade información de control.",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [A("show", "b", at="costo"), A("show", "n", at="no_postselect")],
        ),
        beat(
            "control",
            ("", "Comprobar que el bit se invierte"),
            """La guía añade el control al final del circuito. [[medir]]Primero se miden los qubits activos, como siempre. [[lento]]Después se aplica a cada uno un pulso X lento, una rotación RX de pi, [[otra]]y se vuelve a medir.
             [[esperado]]Si todo fue bien, la segunda medición es la primera invertida. Si no coincide, ese disparo probablemente sufrió un error no Markoviano, lento o correlacionado, y se descarta.
             [[mitigation]]Una nota de versiones: estas herramientas vienen del paquete de utilidades de los addons; en las versiones más recientes del cliente también están en el paquete qiskit mitigation, que además permite controles al inicio del circuito.
             [[limite]]En todo caso, es un detector parcial: no revisa todos los errores, y el pulso de control también tiene imperfecciones.""",
            [
                Flow(
                    [
                        dict(t="medir", s="registro `meas`"),
                        dict(t="X lento", s="RX(π)", color="gold"),
                        dict(t="medir otra vez", s="registro `meas_ps`"),
                        dict(t="¿se invirtió?", s="sí → conservar · no → descartar", color="blue"),
                    ],
                    id="f",
                    stagger=True,
                ),
                T(
                    "también en `qiskit-mitigation` (incluye controles previos al circuito)",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("item", "f", at="medir", i=0),
                A("item", "f", at="lento", i=1),
                A("item", "f", at="otra", i=2),
                A("item", "f", at="esperado", i=3),
                A("show", "n", at="mitigation"),
            ],
        ),
        beat(
            "espectadores",
            ("", "Los qubits vecinos también cuentan"),
            """Un qubit que el circuito no usa puede ser vecino de uno activo. [[vecino]]Por el acoplamiento, ese espectador aporta información sobre errores correlacionados, así que también se mide y se controla.
             [[mapa]]El pase que añade los espectadores usa el mapa de acoplamiento del backend para encontrarlos. [[frac]]Y como el pulso lento es una RX, hace falta un backend con puertas fraccionales.""",
            [
                Graph(
                    [[0, 0], [1, 0], [2, 0], [3, 0], [1, 1], [3, 1]],
                    [[0, 1], [1, 2], [2, 3], [1, 4], [3, 5]],
                    nodeLabels={0: "a", 1: "a", 2: "a", 3: "a", 4: "e", 5: "e"},
                    unit=110,
                    r=24,
                    id="g",
                    hidden=True,
                ),
                T(
                    "a = activo · e = espectador (vecino en el mapa de acoplamiento)",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("show", "g", at="vecino"),
                A("hlnode", "g", at="vecino", t=0.5, i=[0, 1, 2, 3], color="blue"),
                A("hlnode", "g", at="mapa", i=[4, 5], color="gold"),
                A("show", "n", at="mapa"),
            ],
        ),
        beat(
            "circuito",
            ("", "Añadir los controles"),
            """El ejemplo de la guía prepara un GHZ de cuatro qubits y lo transpila para un backend con puertas fraccionales.
             [[passes]]Un PassManager con dos pases de las utilidades de los addons: AddSpectatorMeasures, que mide los espectadores, y AddPostSelectionMeasures, que añade el pulso lento y la segunda medición.
             [[run]]El circuito resultante se ejecuta con Executor, cuatro mil disparos. [[regs]]El resultado trae cuatro registros: meas y spec, antes del pulso, y meas ps y spec ps, después.
             [[auth]]Esta parte necesita una cuenta de IBM y un backend real, así que no la ejecutamos en la verificación.""",
            [
                Code(
                    """from qiskit.transpiler import PassManager, generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, QuantumProgram, Executor
from qiskit_addon_utils.noise_management.post_selection.transpiler.passes import (
    AddPostSelectionMeasures, AddSpectatorMeasures)

backend = QiskitRuntimeService().least_busy(use_fractional_gates=True)
transpiled = generate_preset_pass_manager(optimization_level=3, backend=backend).run(circuit)
post_selection_pm = PassManager([
    AddSpectatorMeasures(backend.coupling_map, add_barrier=True),
    AddPostSelectionMeasures(x_pulse_type="rx"),
])
template_circuit_ps = post_selection_pm.run(transpiled)

program = QuantumProgram(shots=4000)
program.append_circuit_item(template_circuit_ps)
executor_result = Executor(backend).run(program).result()[0]
print(list(executor_result.keys()))   # ['meas', 'spec', 'meas_ps', 'spec_ps']""",
                    id="c",
                    norun=True,
                    size=19,
                )
            ],
            [
                A("hl", "c", at="circuito", range="6-7"),
                A("hl", "c", at="passes", range="8-12"),
                A("hl", "c", at="run", range="14-16"),
                A("hl", "c", at="regs", lines=[17]),
            ],
        ),
        beat(
            "mascara",
            ("", "La máscara decide qué queda"),
            """PostSelector interpreta esos registros. [[selector]]Se crea a partir del circuito con los controles y del mapa de acoplamiento, y compute mask devuelve una máscara booleana con un valor por disparo.
             [[true]]Verdadero significa conservar; falso, descartar. [[estrategias]]Hay dos estrategias, node y edge, y la guía calcula las dos. [[and]]Después las combina con un Y lógico.
             [[resultado]]En el ejemplo se conserva el ochenta y tres por ciento de los disparos.""",
            [
                Code(
                    """from qiskit_addon_utils.noise_management.post_selection import PostSelector

post_selector = PostSelector.from_circuit(
    circuit=template_circuit_ps, coupling_map=backend.coupling_map)
mask_node = post_selector.compute_mask(executor_result, strategy="node")
mask_edge = post_selector.compute_mask(executor_result, strategy="edge")
mask = mask_node & mask_edge
print(f"conservados: {100 * mask.sum() / 4000}%")""",
                    id="c",
                    norun=True,
                    size=21,
                ),
                Out("conservados: 83.3%", id="o", hidden=True),
            ],
            [
                A("hl", "c", at="selector", range="3-4"),
                A("hl", "c", at="estrategias", range="5-6"),
                A("hl", "c", at="and", lines=[7]),
                A("show", "o", at="resultado"),
            ],
        ),
        beat(
            "predice_and",
            ("", "Dos reglas, un Y lógico"),
            """Mira qué exige cada estrategia. [[node]]Node descarta el disparo si algún qubit no invirtió su bit. [[edge]]Edge mira cada arista del mapa de acoplamiento y solo descarta si en alguna arista no se invirtió ninguno de los dos bits.
             [[apuesta]]La guía conserva los disparos que pasan las dos reglas. Antes de ejecutar, apuesta: ¿cuántos disparos conserva node Y edge, comparado con node solo?""",
            [
                Table(
                    ["Estrategia", "Descarta el disparo si…"],
                    [
                        ["node", "algún bit no se invirtió"],
                        ["edge", "en alguna arista no se invirtió ninguno de los dos bits"],
                    ],
                    id="t",
                    stagger=True,
                    size=23,
                )
            ],
            [A("item", "t", at="node", i=0), A("item", "t", at="edge", i=1)],
            ask=predict(
                "`mask_node & mask_edge`, ¿cuántos disparos conserva?",
                [
                    "menos que node",
                    "los mismos que node",
                    "los mismos que edge",
                    "más que node y que edge",
                ],
                "Anotado. Probémoslo con un simulador con ruido de lectura.",
            ),
        ),
        beat(
            "comparar",
            ("", "Las tres máscaras"),
            """Un GHZ de cuatro qubits en línea, con los controles de la guía, en Aer con ruido de lectura y de CNOT. No hace falta backend real. [[ps]]AddPostSelectionMeasures añade el pulso lento y la segunda medida. [[ruido]]El modelo tiene tres por ciento de error de lectura y dos por ciento por CNOT.
             [[selector]]PostSelector se construye con el circuito y las aristas de la línea. [[masks]]Calculamos las dos máscaras y su Y lógico.
             [[res]]Node conserva el setenta y ocho por ciento; edge, casi el noventa y nueve; y node Y edge, exactamente lo mismo que node. Todo disparo que pasa node ya tiene todos sus bits invertidos, así que pasa también edge: el Y lógico no añade ningún filtro. La estrategia estricta es node; edge es la permisiva.""",
            [
                Code(
                    """import numpy as np
from qiskit import QuantumCircuit
from qiskit.transpiler import PassManager
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error
from qiskit_addon_utils.noise_management.post_selection import PostSelector
from qiskit_addon_utils.noise_management.post_selection.transpiler.passes import AddPostSelectionMeasures

ghz = QuantumCircuit(4)
ghz.h(0)
for q in range(3):
    ghz.cx(q, q + 1)
ghz.measure_all()
ghz_ps = PassManager([AddPostSelectionMeasures(x_pulse_type="rx")]).run(ghz)

modelo = NoiseModel()
modelo.add_all_qubit_readout_error(ReadoutError([[0.97, 0.03], [0.03, 0.97]]))
modelo.add_all_qubit_quantum_error(depolarizing_error(0.02, 2), ["cx"])
sim = AerSimulator(noise_model=modelo, seed_simulator=11)
memoria = sim.run(ghz_ps, shots=4000, memory=True).result().get_memory()
bits = lambda i: np.array([[b == "1" for b in reversed(m.split()[i])] for m in memoria])
datos = {"meas": bits(1), "meas_ps": bits(0)}

selector = PostSelector.from_circuit(ghz_ps, [(0, 1), (1, 2), (2, 3)])
mask_node = selector.compute_mask(datos, strategy="node")
mask_edge = selector.compute_mask(datos, strategy="edge")
print(f"node: {mask_node.mean():.1%} · edge: {mask_edge.mean():.1%} · node & edge: {(mask_node & mask_edge).mean():.1%}")""",
                    id="c",
                    size=14,
                ),
                Out(
                    "node: 78.5% · edge: 98.6% · node & edge: 78.5%",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="ps", lines=[14]),
                A("hl", "c", at="ruido", range="16-18"),
                A("hl", "c", at="selector", lines=[24]),
                A("hl", "c", at="masks", range="25-27"),
                A("show", "o", at="res"),
            ],
        ),
        beat(
            "honesto",
            ("", "¿Mejoró el resultado?"),
            """La guía compara la distribución con el ideal: mitad cero cero cero cero, mitad uno uno uno uno. [[antes]]Sin postselección, la fidelidad con la distribución ideal es cero coma nueve tres ocho. [[despues]]Con postselección, cero coma nueve tres dos: en este caso, un poco peor.
             [[leccion]]La lección es importante: la postselección puede mejorar mucho los resultados cuando hay errores no Markovianos, pero no es una solución completa, cuesta disparos, y hay que comprobar su efecto en cada caso.""",
            [
                Hist(
                    [["sin postselección", 0.9385], ["con postselección", 0.9316]],
                    id="h",
                    h=140,
                    ymax=1.05,
                    digits=3,
                    color="teal",
                    hidden=True,
                ),
                Box(
                    "warn",
                    "Mide antes de creer",
                    T("reporta la fracción conservada y compara con y sin filtrar", "body"),
                    id="b",
                    hidden=True,
                ),
            ],
            [A("show", "h", at="antes"), A("show", "b", at="leccion")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Sobre una máscara de postselección.""",
            [T("`mask[i]` vale `True` para uno de tus disparos.", "body")],
            ask=choice(
                "¿Qué significa?",
                [
                    "conservar la muestra `i`",
                    "corregir automáticamente el bit",
                    "volver a ejecutar el disparo",
                ],
                0,
                "Correcto: `True` identifica los disparos que pasan los controles y se conservan.",
                wrong=[None, "La máscara no corrige el estado.", "El disparo ya ocurrió."],
            ),
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Sobre las dos estrategias.""",
            [
                Table(
                    ["Estrategia", "Regla"],
                    [
                        ["node", "descarta si algún bit no se invirtió"],
                        [
                            "edge",
                            "descarta si en alguna arista no se invirtió ninguno de los dos bits",
                        ],
                    ],
                    id="t",
                )
            ],
            ask=choice(
                "¿Cuál conserva más muestras?",
                ["node", "edge"],
                1,
                "Correcto: edge es más permisiva; node descarta por cualquier qubit que falle, y todo disparo que pasa node también pasa edge.",
                wrong=["Node exige que todos los controles pasen.", None],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. Abre el cuaderno de práctica con el comando de abajo. Usa el mismo GHZ de cuatro qubits con controles, sobre Aer. [[n1]]Primero filtras con la máscara node y mides cuánto sube la fidelidad. [[n2]]Después subes el error de lectura hasta que sobreviva menos del sesenta por ciento de los disparos. [[n3]]Y por último escribes tú las máscaras node y edge y las comparas con las de PostSelector.
             [[check]]Cada misión tiene una comprobación: busca la marca verde.""",
            [
                Mission(
                    "practica/p6-postseleccion.py",
                    [
                        (
                            1,
                            "Calcula la máscara `node` y compara la fidelidad con el GHZ antes y después de filtrar.",
                        ),
                        (
                            2,
                            "Sube el error de lectura hasta que `node` conserve menos del 60 % de los disparos.",
                        ),
                        (
                            3,
                            "Escribe `mascara(res, estrategia)` para `node` y `edge`; debe coincidir con `compute_mask`.",
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
            """Dos preguntas para pensar con calma.""",
            [T("Filtrar es gratis en código y caro en disparos.", "subtitle")],
            ask=reflect(
                "Con el error de lectura al diez por ciento sobrevive menos de la mitad de los disparos. ¿Qué información pierdes al descartarlos, y cómo se lo contarías a quien lea tu resultado?",
                "La guía mostró un caso en que filtrar empeoró un poco la fidelidad. ¿Qué comprobaciones harías antes de usar postselección en tu cadena de Ising?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Los controles de inversión de bit detectan algunas fluctuaciones lentas y errores correlacionados.
             [[r2]]Se pueden agregar al circuito en qubits activos y en sus espectadores conectados.
             [[r3]]PostSelector genera una máscara: True conserva y False descarta.
             [[r4]]Mide cuánto descartas; filtrar puede ayudar, pero también reduce la muestra y no corrige todos los errores.""",
            s_post,
            a_post,
        ),
    ],
    sources=["post-selection"],
    practice=[
        "En un conjunto de muestras con controles pre y post, compara las estrategias `node` y `edge` e informa la fracción que conserva cada una."
    ],
)


# ------------------------------------------------------------------ 6.7 NEAT
s_neat, a_neat = resumen(
    [
        "NEAT estima cómo afecta el ruido antes de gastar tiempo de QPU",
        "convierte puertas de un qubit a Clifford y conserva estructura y profundidad",
        "compara simulaciones ideales y ruidosas en PUBs",
        "la simulación aproximada orienta; no garantiza el resultado del hardware",
    ]
)
neat = lesson(
    "p6-neat",
    "Depurar trabajos con NEAT",
    "Usar Noisy Estimator Analyzer Tool para explorar el impacto del ruido y comparar opciones antes de enviar trabajos costosos.",
    [
        "describir qué hace NEAT con un circuito",
        "comparar una simulación ideal con una ruidosa",
        "entender por qué NEAT orienta sin predecir exactamente el QPU",
    ],
    [
        beat(
            "intro",
            ("", "Probar antes de gastar tiempo de QPU"),
            """Antes de enviar un trabajo grande, conviene revisar si el circuito y sus opciones tienen sentido. [[nombre]]NEAT, el Analizador de Ruido para Estimator, ayuda a explorar cómo puede afectar el ruido a las expectativas que quieres medir.
             [[simular]]Usa simulación clásica sobre circuitos equivalentes de tipo Clifford: es mucho más barato que probar cada alternativa en el QPU.
             [[cuidado]]NEAT es una herramienta de análisis y comparación. Sus resultados no son una promesa de lo que devolverá el dispositivo real.""",
            [
                Flow(
                    [
                        dict(t="PUBs de Estimator"),
                        dict(t="circuitos Clifford"),
                        dict(t="simulación ideal y ruidosa"),
                        dict(t="comparar opciones"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="nombre", i=0),
                A("item", "f", at="simular", i=1),
                A("item", "f", at="simular", i=2),
                A("item", "f", at="simular", i=3),
            ],
        ),
        beat(
            "clifford",
            ("", "Cliffordizar sin vaciar el circuito"),
            """Un circuito con rotaciones arbitrarias de un qubit suele ser difícil de simular. [[puertas]]NEAT reemplaza puertas de un qubit que no son Clifford por aproximaciones Clifford.
             [[conserva]]Mantiene las puertas de dos qubits, el número de qubits y la profundidad. [[proxy]]Así conserva una estructura parecida para estudiar cómo crecen los errores, pero ya no es exactamente el circuito original; esa aproximación es parte del análisis.""",
            [
                Row(
                    Box("def", "Se cambia", T("algunas puertas de un qubit", "body"), id="a"),
                    Box(
                        "idea",
                        "Se conserva",
                        T("entrelazamiento, ancho y profundidad", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=20,
                )
            ],
            [A("show", "a", at="puertas"), A("show", "b", at="conserva")],
        ),
        beat(
            "pubs",
            ("", "El circuito se analiza como PUB"),
            """El análisis recibe PUBs, con circuitos ISA y observables ya mapeados al layout. [[isa]]Primero transpila el circuito al backend objetivo y adapta el observable con el layout que produjo el transpilador.
             [[par]]Después creas `Neat` con el backend y conviertes los PUBs a Clifford. [[ideal]]La simulación ideal da una referencia sin ruido. [[ruidoso]]La simulación ruidosa usa un modelo asociado al backend o uno que tú suministres.""",
            [
                Flow(
                    [
                        dict(t="circuito + observable"),
                        dict(t="transpilar a ISA"),
                        dict(t="convertir a Clifford"),
                        dict(t="ideal ↔ ruidoso"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="isa", i=1),
                A("item", "f", at="par", i=2),
                A("item", "f", at="ideal", i=3),
            ],
        ),
        beat(
            "predice_neat",
            ("", "Antes de analizar"),
            """Un circuito espejo de seis qubits: rotaciones aleatorias y capas de CNOT, seguidas de su inverso. [[ideal]]Sin ruido, cada valor esperado de Z vale exactamente uno. [[capas]]Lo analizaremos con una y con seis capas, en el backend falso Sherbrooke.
             [[apuesta]]NEAT da una cifra: la diferencia absoluta media entre el resultado ideal y el ruidoso, en porcentaje. Apuesta cuánto vale con seis capas.""",
            [
                Flow(
                    [
                        dict(t="1 capa", s="2 CX por capa de ida"),
                        dict(t="6 capas", s="seis veces más puertas", color="gold"),
                        dict(t="diferencia media", s="ideal ↔ ruidoso", color="blue"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="capas", i=0),
                A("item", "f", at="capas", t=1, i=1),
                A("item", "f", at="apuesta", i=2),
            ],
            ask=predict(
                "Con 6 capas, la diferencia media entre el resultado ideal y el ruidoso será de…",
                ["menos del 1 %", "alrededor del 5 %", "entre el 15 % y el 20 %", "más del 90 %"],
                "Anotado. Ejecutemos el análisis.",
            ),
        ),
        beat(
            "ejemplo",
            ("", "Comparar ideal y ruidoso"),
            """El ejemplo de la guía, ejecutado en local con el backend falso Sherbrooke. [[espejo]]Un circuito espejo de seis qubits: rotaciones RZ aleatorias y capas de CNOT, seguidas de su inverso, así que idealmente cada valor esperado de Z vale uno. Se generan PUBs con una a seis capas.
             [[neat]]Neat recibe el backend; si no le das un modelo de ruido, usa el del backend. [[cliff]]to clifford convierte los PUBs, [[sim]]e ideal sim y noisy sim los simulan sin ruido y con ruido.
             [[res]]La figura de mérito es la diferencia absoluta media, en porcentaje: crece con la profundidad: de unos tres por ciento con una capa a unos diecisiete con seis. Fijamos la semilla del simulador, así que los números se repiten; sin ella cambiarían un poco en cada ejecución, porque la simulación ruidosa toma muestras.""",
            [
                Code(
                    """import random
import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.debug_tools import Neat
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

random.seed(10)
def generate_circuit(n_qubits, n_layers):
    angles = [[random.random() for q in range(n_qubits)] for s in range(n_layers)]
    qc = QuantumCircuit(n_qubits)
    qubits = list(range(n_qubits))
    for layer in range(n_layers):
        for q in qubits:
            qc.rz(angles[layer][q], q)
        for q in (qubits[::2] if layer % 2 == 0 else qubits[1:n_qubits - 1:2]):
            qc.cx(q, q + 1)
    for layer in range(n_layers)[::-1]:          # el inverso: circuito espejo
        for q in (qubits[::2] if layer % 2 == 0 else qubits[1:n_qubits - 1:2]):
            qc.cx(q, q + 1)
        for q in qubits:
            qc.rz(-angles[layer][q], q)
    return qc

backend = FakeSherbrooke()
pm = generate_preset_pass_manager(backend=backend, optimization_level=0)
isa_qc = pm.run(generate_circuit(6, 3))
obs = ["ZIIIII", "IZIIII", "IIZIII", "IIIZII", "IIIIZI", "IIIIIZ"]
isa_obs = [SparsePauliOp(o).apply_layout(isa_qc.layout) for o in obs]
pubs = [(pm.run(generate_circuit(6, n)), isa_obs) for n in range(1, 7)]

analyzer = Neat(backend)                 # sin modelo propio: el del backend
clifford_pubs = analyzer.to_clifford(pubs)
ideal = analyzer.ideal_sim(clifford_pubs, seed_simulator=1)
noisy = analyzer.noisy_sim(clifford_pubs, seed_simulator=1)
for n, (i, r) in enumerate(zip(ideal, noisy), 1):
    print(n, np.round(np.mean(abs(i - r).vals) * 100, 2))""",
                    id="c",
                    size=19,
                ),
                Out(
                    "1 2.83\n2 4.92\n3 10.48\n4 13.83\n5 17.15\n6 17.19",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="espejo", range="10-24"),
                A("hl", "c", at="neat", lines=[33]),
                A("hl", "c", at="cliff", lines=[34]),
                A("hl", "c", at="sim", range="35-36"),
                A("hl", "c", at="res", range="37-38"),
                A("show", "o", at="res"),
            ],
        ),
        beat(
            "interpreta",
            ("", "Cómo interpretar la diferencia"),
            """Compara el valor ideal con el ruidoso y repite el análisis con distintas profundidades. [[tendencia]]Si la diferencia crece con las capas, el circuito es más sensible al modelo de ruido. También puedes cambiar el modelo: analyzer punto noise model acepta uno propio de Aer, por ejemplo, un dos por ciento de despolarización en cada puerta de dos qubits.
             [[decidir]]Puedes usar ese indicador para comparar circuitos, modificar niveles de resiliencia o escoger factores de ruido. [[modelo]]La simulación Aer no representa todos los fenómenos físicos del QPU y puede subestimar el ruido real.
             [[trabajo]]NEAT evita gastar tiempo de QPU en algunas pruebas exploratorias; el resultado final todavía requiere ejecutar y medir tu circuito real.""",
            [
                Hist(
                    [
                        ["1 capa", 2.83],
                        ["2", 4.92],
                        ["3", 10.48],
                        ["4", 13.83],
                        ["5", 17.15],
                        ["6", 17.19],
                    ],
                    id="g",
                    hidden=True,
                    h=150,
                    w=760,
                    digits=2,
                    ylabel="diferencia media (%)",
                    color="red",
                ),
                Box(
                    "warn",
                    "Proxy, no predicción",
                    T("el modelo de ruido no incluye todos los errores de un QPU", "body"),
                    id="b",
                    hidden=True,
                ),
            ],
            [
                A("show", "g", at="tendencia"),
                A("grow", "g", at="tendencia"),
                A("show", "b", at="modelo"),
            ],
        ),
        beat(
            "reglas",
            ("", "Reglas prácticas"),
            """La guía da unas reglas aproximadas, según la diferencia media absoluta entre los resultados ideal y ruidoso. [[r90]]Si supera el noventa por ciento, probablemente ninguna mitigación ayude.
             [[pea]]Si está por debajo del noventa por ciento, PEA probablemente pueda mejorar los resultados. [[zne]]Y por debajo del ochenta por ciento, también ZNE con plegado de puertas.
             [[app2]]NEAT sirve además para comparar estrategias: la guía prueba cinco juegos de factores de ruido para PEA, y el que da menor diferencia, en ese caso uno, uno coma cinco y dos, sugiere qué opción usar en el experimento real.""",
            [
                Table(
                    ["Diferencia media", "Sugerencia"],
                    [
                        ["> 90 %", "la mitigación probablemente no ayude"],
                        ["< 90 %", "PEA probablemente mejore"],
                        ["< 80 %", "también ZNE con plegado de puertas"],
                    ],
                    id="t",
                    stagger=True,
                    size=25,
                ),
                Hist(
                    [
                        ["[1, 1.1]", 10.9],
                        ["[1, 1.1, 1.2]", 4.64],
                        ["[1, 1.5, 2]", 4.33],
                        ["[1 … 3]", 5.66],
                        ["[1, 4]", 4.53],
                    ],
                    id="h",
                    hidden=True,
                    h=130,
                    w=760,
                    digits=2,
                    color="gold",
                ),
            ],
            [
                A("item", "t", at="r90", i=0),
                A("item", "t", at="pea", i=1),
                A("item", "t", at="zne", i=2),
                A("show", "h", at="app2"),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Sobre la conversión a Clifford.""",
            [T("NEAT prepara una versión simulable del circuito.", "body")],
            ask=choice(
                "¿Qué preserva al convertirlo?",
                [
                    "las puertas de un qubit exactamente",
                    "las puertas de dos qubits, el ancho y la profundidad",
                    "el resultado real que dará el QPU",
                ],
                1,
                "Correcto: reemplaza algunas puertas de un qubit y conserva las puertas de dos qubits, el ancho y la profundidad.",
                wrong=[
                    "Algunas puertas de un qubit se reemplazan.",
                    None,
                    "Es una aproximación para analizar, no una predicción exacta.",
                ],
            ),
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Sobre el uso del resultado.""",
            [
                T(
                    "El modelo de ruido de Aer da una diferencia pequeña entre ideal y ruidoso.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué conclusión es válida?",
                [
                    "el QPU dará exactamente esa diferencia",
                    "el circuito es inmune al ruido",
                    "el modelo sugiere poca desviación y sirve para comparar opciones",
                ],
                2,
                "Correcto: NEAT orienta comparaciones bajo un modelo; no garantiza el resultado del hardware.",
                wrong=[
                    "El QPU puede tener ruido que el modelo no incluye.",
                    "La simulación solo considera los errores modelados.",
                    None,
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. Abre el cuaderno de práctica con el comando de abajo. Usa el backend falso Sherbrooke, sin cuenta ni cola. [[n1]]Primero analizas uno, dos y tres capas y ves cómo crece la diferencia. [[n2]]Después sustituyes el modelo de ruido del backend por uno tuyo, con un dos por ciento de despolarización en cada puerta de dos qubits. [[n3]]Y por último escribes las reglas de la guía como una función: qué técnicas sugiere cada diferencia media.
             [[check]]Cada misión tiene una comprobación: busca la marca verde.""",
            [
                Mission(
                    "practica/p6-neat.py",
                    [
                        (
                            1,
                            "Analiza 1, 2 y 3 capas con el modelo del backend y comprueba que la diferencia crece.",
                        ),
                        (
                            2,
                            "Pasa a `Neat` un modelo de Aer con 2 % de despolarización en `ecr` y compáralo con el del backend.",
                        ),
                        (
                            3,
                            'Escribe `sugerencia(dif)`: `[]`, `["PEA"]` o `["PEA", "ZNE"]` según las reglas de la guía.',
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
            "proyecto",
            ("", "Tu proyecto: mitigar la cadena de espines"),
            """Cierras la parte VI con el hito seis de tu proyecto Ising. [[mide]]Recalculas la magnetización exacta y la de Trotter, y mides cuánto sesga el ruido sin mitigar. [[trex]]Después aplicas TREX a mano, dividiendo por una calibración con el circuito vacío. [[zne]]Y por último extrapolas con ZNE, plegando el circuito, y comparas los tres con el valor exacto.
             [[sim]]Todo corre por defecto en un simulador con el ruido de un backend falso; un interruptor te deja usar un QPU real si tienes tu cuenta. [[res]]Con el simulador, ZNE queda más cerca del exacto que TREX, y TREX más cerca que no mitigar. La mitigación apunta al valor de Trotter sin ruido: la diferencia restante es error de Trotter, y ninguna técnica de esta parte la toca.""",
            [
                M(r"M_z=\tfrac1N\sum_i\langle Z_i\rangle", size=46),
                Table(
                    ["Método", "Qué corrige"],
                    [
                        ["Sin mitigar", "nada: el número a batir"],
                        ["TREX", "sesgo de lectura"],
                        ["ZNE", "sesgo total, por extrapolación"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                ),
                Mission(
                    "practica/proyecto/hito6.py",
                    [
                        (1, "Recalcula el valor exacto y mide el error sin mitigar."),
                        (
                            2,
                            "Aplica TREX: divide la magnetización entre la calibración con el circuito vacío.",
                        ),
                        (
                            3,
                            "Escribe `extrapolar(factores, valores)` con una exponencial y compara los tres métodos.",
                        ),
                    ],
                    title="Proyecto Ising · Hito VI",
                    id="m",
                    hidden=True,
                ),
            ],
            [
                A("item", "t", at="mide", i=0),
                A("item", "t", at="trex", i=1),
                A("item", "t", at="zne", i=2),
                A("show", "m", at="sim"),
            ],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma, para cerrar la parte.""",
            [T("Una cifra barata para decidir antes de gastar QPU.", "subtitle")],
            ask=reflect(
                "NEAT trabaja con una versión Clifford de tu circuito. ¿Qué puede esconder esa aproximación sobre el ruido de tu cadena de Ising?",
                "En el hito seis, ¿qué parte del error que queda atribuyes al ruido y cuál a Trotter? ¿Cómo lo separarías con una medición?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]NEAT analiza PUBs de Estimator con simulaciones ideales y ruidosas.
             [[r2]]Cliffordiza puertas de un qubit y conserva la estructura y profundidad del circuito.
             [[r3]]La comparación ayuda a escoger opciones antes de gastar tiempo de QPU.
             [[r4]]El modelo de Aer es una aproximación; valida el resultado con el hardware real.""",
            s_neat,
            a_neat,
        ),
    ],
    sources=["debug-qiskit-runtime-jobs"],
    practice=[
        "Repite el análisis con una y tres capas de entrelazamiento y compara la diferencia ideal–ruidosa sin asumir que predice el QPU."
    ],
)


LESSONS = [panorama, supresion, mitigacion, configurar, aprender_ruido, postseleccion, neat]
