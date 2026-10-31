"""Parte II · Circuitos y operadores."""

from lib import (
    A,
    Block,
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
)


def resumen(
    items: list[str], marks: tuple[str, ...] = ("r1", "r2", "r3", "r4")
) -> tuple[list[Block], list[Block]]:
    """Escena y acciones de un paso de resumen con una lista que aparece por partes."""
    return [L(items, id="r", stagger=True)], [
        A("item", "r", at=m, i=k) for k, m in enumerate(marks[: len(items)])
    ]


# ------------------------------------------------------------------ 2.1 Construir circuitos
s_cierre, a_cierre = resumen(
    [
        "`QuantumCircuit`: qubits + lista de instrucciones (`data`)",
        "`append`, `compose`, `to_instruction`, `to_gate().control()`, `decompose`",
        "`depth()`: capas en paralelo ≈ tiempo de ejecución",
        "`Parameter` + `assign_parameters`: optimizar una vez, ejecutar muchas",
    ]
)
circuitos = lesson(
    "p2-circuitos",
    "Construir circuitos",
    "QuantumCircuit por dentro: qubits, registros, instrucciones, composición, puertas controladas, profundidad y circuitos con parámetros.",
    [
        "describir un circuito como qubits más una lista de instrucciones",
        "combinar circuitos con `append`, `compose`, `to_instruction` y `to_gate`",
        "crear circuitos con parámetros y asignarles valores",
    ],
    [
        beat(
            "que_es",
            ("", "Qué es un circuito"),
            """Un circuito cuántico simple es una colección de qubits y una lista de instrucciones que actúan sobre ellos.
             [[qb]]Al crear QuantumCircuit de dos, obtienes dos qubits, ordenados del menos significativo, q cero, al más significativo.
             [[reg]]También puedes agrupar qubits y bits clásicos en registros con nombre, y combinar varios en un mismo circuito.
             [[find]]find bit te dice el índice global de un qubit y a qué registro pertenece. Aquí, el único qubit de qreg2 es el qubit dos del circuito.""",
            [
                Code(
                    """from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister, ClassicalRegister

qc = QuantumCircuit(2)

qr1 = QuantumRegister(2, "qreg1")
qr2 = QuantumRegister(1, "qreg2")
cr1 = ClassicalRegister(3, "creg1")
combined = QuantumCircuit(qr1, qr2, cr1)

bit = combined.find_bit(qr2[0])
print("Índice:", bit.index)
print("Registro:", bit.registers)""",
                    id="c",
                    reveal=True,
                    size=23,
                ),
                Out(
                    "Índice: 2\nRegistro: [(QuantumRegister(1, 'qreg2'), 0)]",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("lines", "c", at="qb", to=4),
                A("lines", "c", at="reg", to=9),
                A("lines", "c", at="find", to=13),
                A("show", "o", at="find", t=1.5),
            ],
        ),
        beat(
            "data",
            ("", "La lista de instrucciones"),
            """Cada vez que añades una puerta, se agrega una instrucción al atributo data del circuito. [[ci]]Cada elemento es un CircuitInstruction, con una operación y los qubits sobre los que actúa.
             [[def]]Las instrucciones pueden traer una definición en términos de operaciones más básicas. La X, por ejemplo, se define como un caso particular de la puerta U: U de pi, cero, pi.
             [[dif]]Una diferencia importante de diseño: las instrucciones se tratan como fijas, y sus métodos devuelven instrucciones nuevas; los circuitos, en cambio, se construyen a lo largo de muchas líneas y sus métodos suelen modificarlos.""",
            [
                Code(
                    """qc.x(0)
print(qc.data[0].operation.name, qc.data[0].qubits)
print(qc.data[0].operation.definition)""",
                    id="c",
                ),
                Out(
                    """x (<Qubit register=(2, "q"), index=0>,)
   ┌──────────┐
q: ┤ U(π,0,π) ├
   └──────────┘""",
                    id="o",
                    hidden=True,
                    check=True,
                ),
                Row(
                    Box("def", "Instrucción", T("fija: sus métodos devuelven otra nueva", "body")),
                    Box(
                        "idea",
                        "Circuito",
                        T("se construye paso a paso: sus métodos lo **modifican**", "body"),
                    ),
                    id="r",
                    hidden=True,
                    gap=24,
                ),
            ],
            [
                A("show", "o", at="ci"),
                A("hl", "c", at="ci", lines=[2]),
                A("hl", "c", at="def", lines=[3]),
                A("show", "r", at="dif"),
            ],
        ),
        beat(
            "append",
            ("", "append y compose"),
            """Métodos como h o cx añaden puertas concretas. Para añadir cualquier instrucción usa append, con la instrucción y la lista de qubits.
             [[comp]]Para unir dos circuitos usa compose. Aquí el circuito b, con una Y y una Z, se coloca sobre los qubits uno y tres de un circuito de cuatro.
             [[nuevo]]Atención: compose devuelve un circuito nuevo y no modifica ninguno de los dos, salvo que pases inplace igual a True.""",
            [
                Code(
                    """from qiskit.circuit.library import HGate

qc = QuantumCircuit(1)
qc.append(HGate(), [0])

qc_a = QuantumCircuit(4)
qc_a.x(0)
qc_b = QuantumCircuit(2, name="qc_b")
qc_b.y(0)
qc_b.z(1)
combined = qc_a.compose(qc_b, qubits=[1, 3])""",
                    id="c",
                    size=23,
                ),
                Circ(
                    4,
                    [G("x", 0), G("y", 1, hidden=True), G("z", 3, hidden=True)],
                    id="q",
                    hidden=True,
                ),
                T(
                    "`compose` devuelve un circuito **nuevo** · `inplace=True` para modificar",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="comp", range="6-11"),
                A("show", "q", at="comp"),
                A("gate", "q", at="comp", t=2.5, i=[1, 2]),
                A("show", "n", at="nuevo"),
            ],
        ),
        beat(
            "gate",
            ("", "Instrucciones y puertas propias"),
            """Para organizar circuitos grandes puedes convertir un circuito en una instrucción, con to instruction, y añadirla a otro como una sola caja.
             [[gate]]Si el circuito es unitario, to gate lo convierte en una puerta, que tiene métodos extra. [[ctrl]]Por ejemplo, control, que le añade un qubit de control: la caja qc b solo actúa si el qubit cero vale uno.
             [[dec]]Para ver qué hay dentro, decompose expande cada instrucción en su definición, y devuelve un circuito nuevo.""",
            [
                Code(
                    """inst = qc_b.to_instruction()
qc_a.append(inst, [1, 3])

gate = qc_b.to_gate().control()
qc_a.append(gate, [0, 1, 3])
qc_a.decompose()""",
                    id="c",
                ),
                Circ(
                    4,
                    [
                        G("x", 0),
                        G("box", 1, 3, label="qc_b", hidden=True),
                        dict(g="c", ctrl=[0], q=[1, 3], label="qc_b", hidden=True),
                    ],
                    id="q",
                    hidden=True,
                ),
            ],
            [
                A("show", "q", at="gate"),
                A("gate", "q", at="gate", i=1),
                A("hl", "c", at="ctrl", lines=[4, 5]),
                A("gate", "q", at="ctrl", i=2),
                A("hl", "c", at="dec", lines=[6]),
            ],
        ),
        beat(
            "depth_pred",
            ("", "Profundidad"),
            """La profundidad de un circuito cuenta cuántas capas de puertas, ejecutadas en paralelo, hacen falta para completarlo. Dos puertas sobre qubits distintos pueden ir en la misma capa; sobre el mismo qubit, una detrás de otra.
             [[apuesta]]Con esa regla, apuesta: ¿qué profundidad tiene este circuito de seis puertas?""",
            [Circ(3, [G("h", 0), G("x", 1), G("y", 2), G("cx", 0, 1), G("z", 2), G("h", 1)])],
            ask=predict(
                "¿Cuánto devolverá `qc.depth()`?",
                ["2", "3", "4", "6"],
                "Anotado. Contemos las capas.",
            ),
        ),
        beat(
            "depth",
            ("", "Contar capas"),
            """Contemos. [[cap]]Puertas sobre qubits distintos van en la misma capa. [[seq]]Puertas sobre el mismo qubit, una detrás de otra.
             [[tiempo]]Tres capas: si dijiste seis, contaste puertas, no capas. Como cada puerta tarda, la profundidad se parece al tiempo de ejecución, y es una de las cantidades que deciden si un circuito se puede ejecutar bien en un dispositivo ruidoso.""",
            [
                Circ(
                    3,
                    [G("h", 0), G("x", 1), G("y", 2), G("cx", 0, 1), G("z", 2), G("h", 1)],
                    id="q",
                ),
                Code(
                    "print(qc.depth())",
                    id="c",
                    setup="from qiskit import QuantumCircuit\n\nqc = QuantumCircuit(3)\nqc.h(0)\nqc.x(1)\nqc.y(2)\nqc.cx(0, 1)\nqc.z(2)\nqc.h(1)",
                ),
                Out("3", id="o", hidden=True, check=True),
            ],
            [
                A("cursor", "q", at="cap", col=0),
                A("cursor", "q", at="seq", col=1),
                A("cursor", "q", at="tiempo", col=2),
                A("show", "o", at="tiempo"),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Calcula la profundidad de este circuito.""",
            [Circ(3, [G("h", 0), G("cx", 0, 1), G("cx", 1, 2), G("x", 0)])],
            ask=numeric(
                "¿Cuánto devuelve `qc.depth()`?",
                3,
                "Correcto: la H va en la capa 1, la primera CX en la 2 y la segunda CX en la 3; la X sobre $q_0$ cabe en la capa 3, junto a la segunda CX.",
                tol=0.001,
                hint="La X sobre $q_0$ puede ejecutarse en paralelo con la CX entre $q_1$ y $q_2$.",
                solution=[
                    "Capa 1: H. Capa 2: CX(0,1). Capa 3: CX(1,2) y X(0) a la vez. Profundidad 3."
                ],
            ),
        ),
        beat(
            "parametros",
            ("", "Circuitos con parámetros"),
            """Muchos algoritmos ejecutan muchísimas variaciones del mismo circuito. Construir y optimizar cada una saldría caro.
             [[par]]Por eso Qiskit admite parámetros: un Parameter es un número aún sin definir. [[opt]]Construyes y optimizas el circuito una sola vez, con el parámetro dentro.
             [[asig]]Y justo antes de ejecutar, assign parameters le da un valor concreto. Puedes generar cien variantes en un bucle sin volver a optimizar.
             [[lista]]El atributo parameters lista los parámetros sin asignar.""",
            [
                Code(
                    """from qiskit.circuit import Parameter
from qiskit.transpiler import generate_preset_pass_manager

angle = Parameter("angle")
qc = QuantumCircuit(1)
qc.rx(angle, 0)
qc = generate_preset_pass_manager(
    optimization_level=3, basis_gates=["u", "cx"]).run(qc)

circuits = [qc.assign_parameters({angle: v}) for v in range(100)]
print(qc.parameters)""",
                    id="c",
                    size=23,
                ),
                Out("ParameterView([Parameter(angle)])", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="par", lines=[4]),
                A("hl", "c", at="opt", range="5-8"),
                A("hl", "c", at="asig", lines=[10]),
                A("hl", "c", at="lista", lines=[11]),
                A("show", "o", at="lista"),
            ],
        ),
        beat(
            "nombres",
            ("", "Cambiar el nombre de los parámetros"),
            """Los circuitos de la biblioteca traen parámetros con nombres por defecto, como x de cero. [[vec]]Para renombrarlos, crea un ParameterVector con el prefijo que quieras [[asig]]y asígnalo con assign parameters: ahora se llaman hi de cero, hi de uno, y así.""",
            [
                Code(
                    """from qiskit.circuit.library import z_feature_map
from qiskit.circuit import ParameterVector

circuit = z_feature_map(2)
print(circuit.parameters)
training_params = ParameterVector("hi", 2)
circuit = circuit.assign_parameters(parameters=training_params)
print(circuit.parameters)""",
                    id="c",
                ),
                Out(
                    """ParameterView([ParameterVectorElement(x[0]), ParameterVectorElement(x[1])])
ParameterView([ParameterVectorElement(hi[0]), ParameterVectorElement(hi[1])])""",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="vec", lines=[6]),
                A("hl", "c", at="asig", lines=[7]),
                A("show", "o", at="asig"),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Una pregunta sobre compose.""",
            [
                Code(
                    """a = QuantumCircuit(2)
b = QuantumCircuit(2)
b.h(0)
c = a.compose(b)""",
                    id="c",
                )
            ],
            ask=choice(
                "Después de este código, ¿cuántas instrucciones tiene `a`?",
                ["0", "1", "2", "depende de `b`"],
                0,
                "Correcto: `compose` devuelve un circuito nuevo (`c`, con una H). `a` queda intacto, salvo que uses `inplace=True`.",
                wrong=[
                    None,
                    "Esa H está en `c`, no en `a`.",
                    "No: `a` no se modifica.",
                    "No depende: `compose` nunca modifica `a` sin `inplace=True`.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Primero, inspecciona la lista de instrucciones de un circuito y predice su profundidad antes de calcularla. [[n2]]Después, reordena un estado GHZ de seis qubits para que tenga menos capas sin cambiar el estado: la escalera de CNOTs tiene profundidad seis, y se puede bajar a cuatro.
             [[n3]]Y por último, construye una familia de veintiún circuitos a partir de uno solo con un parámetro, y comprueba que siguen la curva teórica.""",
            [
                Exercise(
                    "p2-circuitos/profundidad",
                    "Recorre `qc.data` y apuesta cuánto vale `qc.depth()`: escribe tu apuesta en `prediccion` y compruébala después.",
                    level=1,
                    id="e1",
                    hidden=True,
                    hints=[
                        "La profundidad cuenta capas, no puertas: una puerta espera a que sus qubits queden libres.",
                        "Recorre la lista y anota en qué capa cae cada puerta; las de qubits distintos comparten capa.",
                        "Dibuja el circuito con `qc.draw()` y cuenta las columnas.",
                    ],
                ),
                Exercise(
                    "p2-circuitos/ghz-menos-profundo",
                    "Prepara el mismo GHZ de 6 qubits con profundidad 4 o menos, usando solo puertas de uno y dos qubits.",
                    level=2,
                    id="e2",
                    hidden=True,
                    hints=[
                        "La escalera de CNOTs tiene profundidad seis porque cada `cx` espera a la anterior.",
                        "Un qubit que ya está entrelazado con el 0 también puede hacer de control: busca CNOTs que puedan ir en la misma capa.",
                        "Cada capa de CNOTs puede duplicar el número de qubits ya entrelazados.",
                    ],
                ),
                Exercise(
                    "p2-circuitos/familia-theta",
                    r"Completa `base` una sola vez: una RX con el parámetro `theta` en el qubit 0, una CX de 0 a 1 y la medición de todo. "
                    r"Después llena `familia` con 21 circuitos derivados de `base`, con $\theta$ de 0 a $\pi$ (los dos extremos incluidos), "
                    r"para que $P(11)=\sin^2(\theta/2)$. Trampa: ningún circuito de `familia` conserva `theta` libre, pero `base` sí lo conserva.",
                    level=3,
                    id="e3",
                    hidden=True,
                    hints=[
                        "Construye `base` una vez y deriva de ella las 21 variantes, sin repetir el circuito.",
                        "El método `assign_parameters` fija el parámetro y devuelve un circuito nuevo.",
                        "Necesitas 21 valores equiespaciados entre 0 y $\\pi$ y un circuito por cada valor.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma, conectadas con tu proyecto.""",
            [T("La profundidad es tiempo, y el tiempo es ruido.", "subtitle")],
            ask=reflect(
                "¿Por qué crees que a un computador cuántico real le importa más la **profundidad** que el número total de puertas?",
                "En tu proyecto Ising, cada paso de tiempo es el mismo circuito con otros ángulos. ¿Cómo usarías `compose` y `Parameter` para construir 10 pasos?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Un circuito es una colección de qubits y una lista de instrucciones. [[r2]]append, compose, to instruction, to gate y decompose te dejan combinar y organizar circuitos.
             [[r3]]La profundidad cuenta capas en paralelo. [[r4]]Y los parámetros permiten optimizar una vez y ejecutar muchas variantes.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["construct-circuits"],
    practice=[
        "Construye un GHZ de 5 qubits como `to_gate()` y úsalo dos veces en un circuito de 10 qubits con `append`; compara `depth()` antes y después de `decompose()`.",
        "Crea un circuito con dos parámetros `θ` y `φ` y genera una cuadrícula de 10×10 variantes con `assign_parameters`.",
    ],
)

# ------------------------------------------------------------------ 2.2 Medir
s_cierre, a_cierre = resumen(
    [
        "se mide en la base $Z$: 0 o 1 con $p=|\\langle q|0\\rangle|^2$, $|\\langle q|1\\rangle|^2$",
        "`measure(q, c)` · `Measure()` con `append`",
        "`measure_all()`: registro `meas` + barrera · `measure_active()`: solo qubits usados",
        "Sampler necesita mediciones; Estimator no las admite",
    ]
)
medir = lesson(
    "p2-medir",
    "Medir qubits",
    "La medición en la base computacional y las cuatro formas de añadirla a un circuito: measure, Measure, measure_all y measure_active.",
    [
        "explicar qué devuelve medir un qubit en la base $Z$",
        "elegir entre `measure`, `measure_all` y `measure_active`",
        "saber cuándo un circuito debe o no debe llevar mediciones",
    ],
    [
        beat(
            "base",
            ("", "Medir en la base Z"),
            """Para obtener información de un qubit hay que medirlo y guardar el resultado en un bit clásico.
             [[z]]En Qiskit se mide en la base computacional, la de la matriz de Pauli Z. [[res]]El resultado es cero, con probabilidad igual al módulo al cuadrado del solapamiento con el estado cero, o uno, con la probabilidad del estado uno.
             [[val]]Los autovalores de Z son más uno y menos uno: el bit cero corresponde al resultado más uno, y el bit uno al menos uno.""",
            [
                M(
                    r"|q\rangle\ \xrightarrow{\text{medir}}\ \begin{cases}0\ (+1) & p_0=|\langle 0|q\rangle|^2\\ 1\ (-1) & p_1=|\langle 1|q\rangle|^2\end{cases}",
                    size=46,
                ),
                Box(
                    "def",
                    "Base computacional",
                    T(
                        "autoestados de $Z$: $|0\\rangle$ (valor $+1$) y $|1\\rangle$ (valor $-1$)",
                        "body",
                    ),
                    id="b",
                    hidden=True,
                ),
            ],
            [A("show", "b", at="val")],
        ),
        beat(
            "measure",
            ("", "measure"),
            """La forma más directa es el método measure: el primer argumento son los qubits y el segundo, los bits clásicos donde se guarda cada resultado.
             [[todos]]Con range de cinco en ambos, cada qubit va a su bit. [[uno]]Pero puedes elegir: aquí se mide solo el qubit uno y se guarda en el bit cero.
             [[clase]]También existe la clase Measure, que se añade con append como cualquier otra instrucción, indicando qubits y bits.""",
            [
                Code(
                    """from qiskit import QuantumCircuit
from qiskit.circuit import Measure

qc = QuantumCircuit(5, 5)
qc.x([0, 1, 4])
qc.measure(range(5), range(5))

qc2 = QuantumCircuit(3, 1)
qc2.x([0, 2])
qc2.measure(1, 0)

qc3 = QuantumCircuit(3, 1)
qc3.append(Measure(), [0], [0])""",
                    id="c",
                    size=23,
                ),
                Circ(
                    3, [G("x", 0), G("x", 2), G("measure", 1, c=0)], clbits=1, id="q", hidden=True
                ),
            ],
            [
                A("hl", "c", at="todos", range="4-6"),
                A("hl", "c", at="uno", range="8-10"),
                A("show", "q", at="uno"),
                A("hl", "c", at="clase", range="12-13"),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """El primer circuito de la escena anterior pone X en los qubits cero, uno y cuatro, y mide los cinco en sus bits.""",
            [
                Code("""qc = QuantumCircuit(5, 5)
qc.x([0, 1, 4])
qc.measure(range(5), range(5))""")
            ],
            ask=choice(
                "¿Qué cadena de bits devuelve siempre?",
                ["`'11001'`", "`'10011'`", "`'11100'`", "`'00111'`"],
                1,
                "Correcto: el bit 0 va a la **derecha**. Los bits 0, 1 y 4 valen 1: `'10011'`.",
                wrong=[
                    "Esa sería la lectura con el bit 0 a la izquierda; Qiskit lo pone a la derecha.",
                    None,
                    "Los qubits con X son 0, 1 y 4, no 2, 3 y 4.",
                    "Revisa qué qubits llevan X: 0, 1 y 4.",
                ],
            ),
        ),
        beat(
            "all_pred",
            ("", "Antes de medir todo"),
            """Una apuesta. Este circuito de tres qubits ya tiene un bit clásico, y ponemos una X en los qubits cero y dos.
             [[cual]]Ahora llamamos a measure all. ¿Cuántos bits clásicos tendrá el circuito cuando termine?""",
            [
                Code(
                    """from qiskit import QuantumCircuit

qc = QuantumCircuit(3, 1)
qc.x([0, 2])
qc.measure_all()
print(qc.num_clbits)""",
                    id="c",
                    size=26,
                )
            ],
            [A("hl", "c", at="cual", lines=[6])],
            ask=predict(
                "Tras `measure_all()`, ¿cuántos bits clásicos tiene el circuito?",
                ["1", "3", "4", "6"],
                "Anotado. Veamos qué hace measure all.",
            ),
        ),
        beat(
            "all",
            ("", "measure_all"),
            """measure all no necesita argumentos y sirve para circuitos sin bits clásicos. [[reg]]Crea un registro nuevo llamado meas, con un bit por qubit, y guarda el qubit i en el bit i. [[bar]]Además añade una barrera antes de medir.
             [[nuevo]]Ojo: si el circuito ya tenía bits clásicos, measure all añade otro registro aparte. Aquí, el registro c original se queda vacío, en cero, y los resultados van a meas. En total son cuatro bits: uno de c y tres de meas.""",
            [
                Code(
                    """qc = QuantumCircuit(3, 1)
qc.x([0, 2])
qc.measure_all()""",
                    id="c",
                ),
                Circ(
                    3,
                    [
                        G("x", 0),
                        G("x", 2),
                        G("barrier", hidden=True),
                        G("measure", 0, c=1, hidden=True),
                        G("measure", 1, c=2, hidden=True),
                        G("measure", 2, c=3, hidden=True),
                    ],
                    clbits=4,
                    clabels=["c₀", "meas₀", "meas₁", "meas₂"],
                    id="q",
                    cidx=True,
                ),
                T(
                    "`c` sigue ahí, sin usar · los resultados van a `meas`",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("gate", "q", at="reg", i=[3, 4, 5]),
                A("gate", "q", at="bar", i=2),
                A("show", "n", at="nuevo"),
            ],
        ),
        beat(
            "active",
            ("", "measure_active"),
            """measure active es parecido, pero mide solo los qubits que tienen alguna operación, los que no están ociosos. [[ej]]Aquí, los qubits cero y dos; el uno no se toca.
             [[reg]]El registro nuevo tiene tantos bits como qubits medidos: dos.""",
            [
                Code(
                    """qc = QuantumCircuit(3, 1)
qc.x([0, 2])
qc.measure_active()""",
                    id="c",
                ),
                Circ(
                    3,
                    [
                        G("x", 0),
                        G("x", 2),
                        G("barrier"),
                        G("measure", 0, c=1, hidden=True),
                        G("measure", 2, c=2, hidden=True),
                    ],
                    clbits=3,
                    clabels=["c₀", "meas₀", "meas₁"],
                    id="q",
                    cidx=True,
                ),
            ],
            [A("gate", "q", at="ej", i=[3, 4])],
        ),
        beat(
            "primitivas",
            ("", "¿Medir o no medir?"),
            """Una regla práctica que usarás todo el tiempo. [[s]]Los circuitos que envías a Sampler deben llevar mediciones: Sampler devuelve precisamente esos bits.
             [[e]]Los circuitos que envías a Estimator no deben llevarlas: Estimator añade por su cuenta lo necesario para medir los observables que le pidas.
             [[mid]]Y en el hardware de IBM también se puede medir en medio del circuito; lo verás con los circuitos dinámicos.""",
            [
                Row(
                    Box("def", "Sampler", T("**con** mediciones", "body"), id="s", hidden=True),
                    Box("warn", "Estimator", T("**sin** mediciones", "body"), id="e", hidden=True),
                    gap=30,
                ),
                T(
                    "medición a mitad de circuito → circuitos dinámicos (Parte VII)",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [A("show", "s", at="s"), A("show", "e", at="e"), A("show", "n", at="mid")],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Una última pregunta.""",
            [
                Code("""qc = QuantumCircuit(4)
qc.h(0)
qc.cx(0, 2)
qc.measure_active()""")
            ],
            ask=numeric(
                "¿Cuántos bits tiene el registro que crea `measure_active()`?",
                2,
                "Correcto: solo los qubits 0 y 2 tienen operaciones, así que se miden dos.",
                tol=0.001,
                hint="Cuenta los qubits que tienen al menos una puerta.",
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Primero, predice cuántos bits clásicos tiene un circuito después de measure all y compruébalo. [[n2]]Después, cambia los argumentos de measure para que el qubit dos se guarde en el bit cero.
             [[n3]]Y por último, entrelaza los qubits uno y tres de un circuito de cinco, mídelos con measure active, y prepara su copia sin mediciones para Estimator.""",
            [
                Exercise(
                    "p2-medir/bits-clasicos",
                    "Este circuito ya tenía un bit clásico. Apuesta en `prediccion` cuántos bits clásicos tiene después de `measure_all()`.",
                    level=1,
                    id="e1",
                    hidden=True,
                    hints=[
                        "`measure_all()` mide todos los qubits.",
                        "No reutiliza el registro que ya existía: crea uno nuevo.",
                        "Cuenta el bit que ya estaba y un bit más por cada qubit medido.",
                    ],
                ),
                Exercise(
                    "p2-medir/qubit-al-bit",
                    "Cambia los argumentos de `measure` para que el qubit 2 se guarde en el bit 0 y el resultado sea `'01'`.",
                    level=2,
                    id="e2",
                    hidden=True,
                    hints=[
                        "El primer argumento de `measure` son los qubits y el segundo, los bits: el qubit de cada posición va al bit de la misma posición.",
                        "En la cadena de bits clásicos, el bit 0 va a la derecha. Para `'01'`, el bit 0 vale 1 y el bit 1 vale 0.",
                        "Fíjate en qué qubit vale 1 y en qué bit debe quedar ese valor; el otro qubit ocupa el bit que sobra.",
                    ],
                ),
                Exercise(
                    "p2-medir/bell-1-3",
                    "`bell13` tiene 5 qubits, pero solo el 1 y el 3 deben quedar entrelazados y medidos, con `measure_active()`. Deja en `para_estimator` el mismo circuito sin mediciones; `bell13` conserva las suyas.",
                    level=3,
                    id="e3",
                    hidden=True,
                    hints=[
                        "Un Bell se prepara con una `H` y una `cx`; aquí actúan sobre los qubits 1 y 3.",
                        "`measure_active()` mide solo los qubits que usaste: el circuito queda con dos bits clásicos.",
                        "Estimator no admite mediciones, y `QuantumCircuit` tiene un método `remove_final_measurements` que las quita; elige si lo aplicas al original o a una copia.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma. Escribe con tus palabras; lo que escribas se guarda en el navegador.""",
            [T("Sampler devuelve bits; Estimator devuelve promedios.", "subtitle")],
            ask=reflect(
                "¿Por qué crees que Sampler necesita que el circuito termine en mediciones y Estimator, en cambio, no las admite? Piensa en lo que devuelve cada uno.",
                "En tu proyecto Ising quieres la magnetización media de la cadena. ¿Usarías Sampler o Estimator, y qué le pasarías?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Se mide en la base Z.[[r2]]measure te da control total, y Measure es la misma operación como instrucción. [[r3]]measure all mide todo en un registro nuevo y measure active, solo lo que se usó.
             [[r4]]Y recuerda: Sampler con mediciones, Estimator sin ellas.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["measure-qubits"],
    practice=[
        "Mide un estado de Bell en la base $X$: añade una H a cada qubit antes de `measure_all()` y compara los conteos con la base $Z$.",
        "Usa `qiskit.circuit.random.random_circuit(4, 3, measure=True)` y cuenta cuántas mediciones tiene.",
    ],
)

# ------------------------------------------------------------------ 2.3 Orden de bits
s_cierre, a_cierre = resumen(
    [
        "diagramas: $q_0$ arriba",
        "enteros: el bit $k$ vale $2^k$ (bit 0 = menos significativo)",
        "cadenas: el bit 0 a la **derecha**",
        "vector de estado: índice $x$ ↔ $|x\\rangle$ · `reverse_bits` solo cambia el dibujo",
    ]
)
orden = lesson(
    "p2-orden-bits",
    "El orden de los bits",
    "Little-endian en Qiskit: cómo se ordenan los qubits en diagramas, enteros, cadenas, vectores de estado y matrices de puertas.",
    [
        "leer correctamente una cadena de bits de Qiskit",
        "pasar de un índice del vector de estado al estado de la base",
        "escribir la matriz de una CX con la convención de Qiskit",
    ],
    [
        beat(
            "intro",
            ("", "Un detalle que confunde a todos"),
            """Con n qubits, los numeramos de cero a n menos uno. La pregunta es en qué orden se escriben, en memoria y en pantalla. Cada programa elige una convención, y Qiskit usa la llamada little endian.
             [[lista]]Un circuito guarda sus qubits en una lista, y el índice en esa lista es la etiqueta del qubit. [[diag]]En los diagramas, el qubit cero está arriba y el último, abajo.""",
            [
                T("El orden de los bits", "title"),
                Code(
                    '''qc = QuantumCircuit(2)
qc.qubits[0]     # el qubit "0"''',
                    id="c",
                    hidden=True,
                    setup="from qiskit import QuantumCircuit",
                ),
                Circ(2, [G("x", 1)], id="q", hidden=True),
            ],
            [A("show", "c", at="lista"), A("show", "q", at="diag")],
        ),
        beat(
            "cadena_pred",
            ("", "Antes de leer la cadena"),
            """Una apuesta. Ponemos una X en el qubit uno, el de abajo, y medimos los dos qubits. [[cual]]Qiskit nos devuelve una cadena de dos bits. ¿Cuál crees que será?""",
            [
                Circ(
                    2,
                    [G("x", 1), G("barrier"), G("measure", 0, c=0), G("measure", 1, c=1)],
                    clbits=2,
                    creg="meas",
                )
            ],
            ask=predict(
                "¿Qué cadena devolverá `get_counts()`?",
                ["`'01'`", "`'10'`", "`'11'`", "`'00'`"],
                "Anotado. Veamos qué imprime.",
            ),
        ),
        beat(
            "enteros",
            ("", "Enteros y cadenas"),
            """Al leer los bits como un número, el bit cero es el menos significativo: cada bit k vale dos a la k. [[ej]]Si ponemos una X en el qubit uno y medimos, el bit cero vale cero y el bit uno vale uno: el número dos.
             [[cad]]Y al escribirlos como cadena, el bit n menos uno va a la izquierda y el bit cero a la derecha, como escribimos los números: el dígito más significativo primero.
             [[asi]]Por eso Qiskit imprime uno cero, aunque el qubit que cambiamos sea el uno. Si apostaste por cero uno, es el error más común: leer la cadena con el qubit cero a la izquierda.""",
            [
                Code(
                    """from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

qc = QuantumCircuit(2)
qc.x(1)
qc.measure_all()
print(StatevectorSampler().run([qc]).result()[0].data.meas.get_counts())""",
                    id="c",
                ),
                Out("{'10': 1024}", id="o", hidden=True, check=True),
                M(
                    r"\underbrace{1}_{q_1}\ \underbrace{0}_{q_0}\ =\ 1\cdot2^1+0\cdot2^0=2",
                    id="m",
                    hidden=True,
                    size=42,
                ),
            ],
            [A("show", "m", at="ej"), A("show", "o", at="cad"), A("emph", "o", at="asi")],
        ),
        beat(
            "estados",
            ("", "Estados desde una cadena"),
            """Lo mismo vale al crear estados a partir de una cadena. [[mas]]Statevector from label cero más pone el qubit cero en más y el qubit uno en cero, porque la etiqueta de la derecha es la del qubit cero.
             [[prob]]Sus probabilidades: mitad cero cero, mitad cero uno.
             [[amp]]Y en el vector de estado, la amplitud en el índice x corresponde al estado de la base x escrito en binario: el índice uno es cero uno; el índice dos es uno cero.""",
            [
                Code(
                    """from qiskit.quantum_info import Statevector

sv = Statevector.from_label("0+")
print(sv.probabilities())   # índices 0, 1, 2, 3
print(sv[1])   # amplitud de |01>
print(sv[2])   # amplitud de |10>""",
                    id="c",
                ),
                Out(
                    """[0.5 0.5 0.  0. ]
(0.7071067811865475+0j)
0j""",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="mas", lines=[3]),
                A("show", "o", at="prob"),
                A("hl", "c", at="amp", lines=[5, 6]),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Un vector de estado de tres qubits.""",
            [M(r"\text{sv}=[0,\ 0,\ 0,\ 0,\ 0,\ 0,\ 1,\ 0]", size=44)],
            ask=choice(
                "La única amplitud no nula está en el índice 6. ¿Qué qubits valen 1?",
                ["$q_0$ y $q_1$", "$q_1$ y $q_2$", "$q_0$ y $q_2$", "solo $q_2$"],
                1,
                "Correcto: $6=110_2$, así que $q_2=1$, $q_1=1$ y $q_0=0$.",
                wrong=[
                    "Eso sería el índice $3=011_2$.",
                    None,
                    "Eso sería el índice $5=101_2$.",
                    "Eso sería el índice $4=100_2$.",
                ],
            ),
        ),
        beat(
            "cx",
            ("", "La matriz de la CX"),
            """Las puertas interpretan su lista de qubits a su manera, pero las controladas suelen seguir el orden control, objetivo. cx de cero, uno: control en el qubit cero, objetivo en el uno.
             [[trans]]Con las convenciones de Qiskit, esta CX intercambia cero uno con uno uno: es decir, cuando el qubit cero, el de la derecha, vale uno, invierte el de la izquierda.
             [[mat]]Su matriz, en el orden cero cero, cero uno, uno cero, uno uno, no es la que aparece en muchos libros: allí el control suele ser el qubit de la izquierda.""",
            [
                Row(
                    Circ(2, [G("cx", 0, 1)], id="q"),
                    M(
                        r"|0\gold{1}\rangle\leftrightarrow|1\gold{1}\rangle",
                        id="t",
                        hidden=True,
                        size=44,
                    ),
                    gap=40,
                ),
                M(
                    r"\mathrm{CX}_{0\to1}=\begin{pmatrix}1&0&0&0\\0&0&0&1\\0&0&1&0\\0&1&0&0\end{pmatrix}",
                    id="m",
                    hidden=True,
                    size=42,
                ),
                T(
                    "muchos libros ponen el control en el qubit de la izquierda y obtienen otra matriz",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [A("show", "t", at="trans"), A("show", "m", at="mat"), A("show", "n", at="mat", t=2)],
        ),
        beat(
            "reverse",
            ("", "Cambiar el orden"),
            """Si prefieres ver el qubit cero abajo, draw acepta reverse bits igual a True. [[dib]]Eso solo cambia el dibujo; el circuito es el mismo y la X sigue actuando sobre el qubit cero.
             [[met]]En cambio, el método reverse bits del circuito devuelve un circuito nuevo con las etiquetas invertidas: ahí la X sí actúa sobre el qubit uno.
             [[prim]]Y una nota sobre las primitivas: los resultados en bits de Sampler y Estimator de IBM vienen en orden big endian por defecto, mientras que Executor usa little endian.""",
            [
                Code(
                    """qc = QuantumCircuit(2)
qc.x(0)
qc.draw(reverse_bits=True)     # solo el dibujo
qc2 = qc.reverse_bits()        # circuito nuevo: X sobre q1""",
                    id="c",
                ),
                Row(
                    Circ(2, [G("x", 1)], qlabels=["q₁", "q₀"], id="a", hidden=True),
                    Circ(2, [G("x", 1)], id="b", hidden=True),
                    gap=60,
                ),
                T(
                    "primitivas de IBM: Sampler y Estimator → big-endian · Executor → little-endian",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="dib", lines=[3]),
                A("show", "a", at="dib"),
                A("hl", "c", at="met", lines=[4]),
                A("show", "b", at="met"),
                A("show", "n", at="prim"),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Un circuito con tres qubits.""",
            [
                Circ(
                    3,
                    [
                        G("x", 2),
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
                "¿Qué entero devuelve `get_int_counts()`?",
                4,
                "Correcto: solo $q_2=1$, así que $2^2=4$ (la cadena es `'100'`).",
                tol=0.001,
                hint="Cada qubit $k$ con valor 1 aporta $2^k$.",
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Primero, predice la cadena de bits de un circuito con X en los qubits cero y dos. [[n2]]Después, cambia las X de un circuito para preparar el estado cero uno uno.
             [[n3]]Y por último, escribe una función que prepare el estado de la base con el índice que le pidas, para cualquier número de qubits.""",
            [
                Exercise(
                    "p2-orden-bits/cadena-de-bits",
                    "Este circuito pone una X en los qubits 0 y 2. Escribe en `prediccion`, entre comillas, la cadena de bits que devuelve Qiskit.",
                    level=1,
                    id="e1",
                    hidden=True,
                    hints=[
                        "El qubit 0 es el bit menos significativo.",
                        "En una cadena de bits, el bit 0 va a la derecha.",
                        r"Escribe, de izquierda a derecha, el valor de $q_2$, de $q_1$ y de $q_0$.",
                    ],
                ),
                Exercise(
                    "p2-orden-bits/preparar-011",
                    r"Cambia las X para preparar $|q_2q_1q_0\rangle=|011\rangle$.",
                    level=2,
                    id="e2",
                    hidden=True,
                    hints=[
                        "Hoy la X está en el qubit equivocado.",
                        r"Lee el estado de derecha a izquierda: el último dígito es el qubit 0. Los dígitos que valen 1 piden una X.",
                        "Puede que necesites más de una X, cada una en su qubit.",
                    ],
                ),
                Exercise(
                    "p2-orden-bits/preparar",
                    "Escribe `preparar(k, n)`: devuelve un circuito de `n` qubits, sin mediciones, cuyo vector de estado tiene toda la amplitud en el índice `k` (`k` es el índice de la base, de 0 a $2^n-1$). Ojo: el qubit 0 es el bit menos significativo de `k`, no el primero que escribes. Por ejemplo, `preparar(5, 4)` deja la amplitud en el índice 5, que es $0101_2$.",
                    level=3,
                    id="e3",
                    hidden=True,
                    hints=[
                        "Piensa en `k` escrito en binario: cada bit de `k` decide si su qubit empieza en 0 o en 1.",
                        "Recorre los `n` qubits con un `for` y decide, qubit a qubit, si necesita una X.",
                        "Un desplazamiento y una máscara de bits te dan el bit `j` de `k`.",
                    ],
                ),
                Exercise(
                    "p2-orden-bits/preparar-roto",
                    "Esta `preparar(k, n)` debería dejar toda la amplitud en el índice `k`, pero con `preparar(5, 4)` la deja en otro. Encuentra el error y corrígelo.",
                    level=2,
                    kind="fix",
                    id="e4",
                    hidden=True,
                    hints=[
                        "Imprime las probabilidades de `preparar(5, 4)` y busca el índice con probabilidad 1: no es el 5.",
                        "`format(k, '04b')` escribe el bit más significativo primero, pero el qubit 0 es el menos significativo.",
                        "El bucle recorre los bits de izquierda a derecha y numera los qubits en ese orden. Recórrelos al revés.",
                    ],
                ),
            ],
            [
                A("show", "e1", at="n1"),
                A("show", "e2", at="n2"),
                A("show", "e3", at="n3"),
                A("show", "e4", at="n3", t=1),
            ],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma. Escribe con tus palabras; lo que escribas se guarda en el navegador.""",
            [T("La convención es arbitraria; lo que importa es no mezclar dos.", "subtitle")],
            ask=reflect(
                "En el diagrama el qubit 0 está arriba, pero en la cadena de bits va a la derecha. ¿Cómo se lo explicarías a alguien para que no se confunda al leer los conteos?",
                "En tu proyecto Ising mides cada espín. En la cadena `'0010'`, ¿qué carácter corresponde al espín 0 y cómo lo sacarías en código?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]En los diagramas, el qubit cero está arriba. [[r2]]Como número, el bit cero es el menos significativo. [[r3]]Como cadena, el bit cero va a la derecha.
             [[r4]]Y en el vector de estado, el índice x es el estado x en binario. reverse bits en draw solo cambia el dibujo.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["bit-ordering"],
    practice=[
        "Calcula a mano `Operator(CXGate())` y compáralo con la salida de Qiskit; luego haz lo mismo con `qc.cx(1, 0)`.",
        "Prepara $|q_2q_1q_0\\rangle=|110\\rangle$ con puertas X y verifica con `Statevector(qc).probabilities_dict()`.",
    ],
)

# ------------------------------------------------------------------ 2.4 Biblioteca
s_cierre, a_cierre = resumen(
    [
        "puertas estándar: `HGate`, `MCXGate`… con `append`",
        "N-local (`n_local`) y codificación de datos (`zz_feature_map`): con parámetros",
        "evolución temporal (`PauliEvolutionGate`) y referencia (`quantum_volume`, IQP, Grover)",
        "aritmética: `FullAdderGate`",
    ]
)
biblioteca = lesson(
    "p2-biblioteca",
    "La biblioteca de circuitos",
    "Puertas estándar, circuitos N-local, codificación de datos, evolución temporal, circuitos de referencia y aritmética.",
    [
        "añadir puertas de la biblioteca con `append`",
        "usar circuitos con parámetros como `n_local` y `zz_feature_map`",
        "reconocer las familias de circuitos que ofrece la biblioteca",
    ],
    [
        beat(
            "intro",
            ("", "Piezas ya hechas"),
            """La biblioteca de circuitos de Qiskit es una colección de bloques listos para usar: ahorras tiempo de investigación, de escritura y de depuración.
             [[fam]]Incluye circuitos populares, circuitos difíciles de simular clásicamente y circuitos para medir el rendimiento del hardware. Son seis familias.""",
            [
                T("La biblioteca de circuitos", "title"),
                Flow(
                    [
                        dict(t="Puertas", s="estándar"),
                        dict(t="N-local", s="variacionales"),
                        dict(t="Codificación", s="de datos"),
                        dict(t="Evolución", s="temporal"),
                        dict(t="Referencia", s="y complejidad"),
                        dict(t="Aritmética", s="clásica"),
                    ],
                    id="f",
                    stagger=True,
                ),
            ],
            [A("item", "f", at="fam", i=k, t=k * 0.5) for k in range(6)],
        ),
        beat(
            "puertas",
            ("", "Puertas estándar"),
            """La biblioteca también contiene las puertas estándar: desde las fundamentales, como UGate, hasta puertas de muchos qubits que normalmente hay que construir con puertas de uno y dos.
             [[mcx]]Por ejemplo, MCXGate de tres es una X con tres controles. [[app]]Para añadir una puerta importada usas append: primero la puerta y luego la lista de qubits.""",
            [
                Code(
                    """from qiskit import QuantumCircuit
from qiskit.circuit.library import HGate, MCXGate

qc = QuantumCircuit(4)
qc.append(HGate(), [0])
qc.append(MCXGate(3), [0, 1, 2, 3])""",
                    id="c",
                ),
                Circ(
                    4,
                    [
                        G("h", 0),
                        dict(g="c", ctrl=[0, 1, 2], q=[3], base="x", label="X", hidden=True),
                    ],
                    id="q",
                ),
            ],
            [A("gate", "q", at="mcx", i=1), A("hl", "c", at="app", lines=[5, 6])],
        ),
        beat(
            "nlocal_pred",
            ("", "Antes de contar parámetros"),
            """Los circuitos N-local alternan capas de rotaciones de un qubit con capas de puertas que entrelazan. Este es de tres qubits, con rotaciones RX y entrelazamiento CZ. [[cual]]Por defecto repite el bloque varias veces. ¿Cuántos parámetros crees que tendrá?""",
            [
                Code(
                    """from qiskit.circuit.library import n_local

two_local = n_local(3, "rx", "cz")
print(two_local.num_parameters)""",
                    id="c",
                )
            ],
            [A("hl", "c", at="cual", lines=[4])],
            ask=predict(
                "¿Cuántos parámetros tiene `two_local`?",
                ["3", "6", "9", "12"],
                "Anotado. Veamos cómo se construye.",
            ),
        ),
        beat(
            "nlocal",
            ("", "Circuitos N-local"),
            """Contemos. [[var]]Estos circuitos son muy usados en los algoritmos variacionales, porque producen una gran variedad de estados: el algoritmo ajusta los ángulos hasta encontrar el estado que buscas.
             [[ej]]Por defecto el bloque se repite tres veces y se termina con una capa de rotaciones: cuatro capas de tres ángulos, doce parámetros. Si dijiste nueve, olvidaste la capa final.
             [[asig]]Y como cualquier circuito con parámetros, se asignan con un diccionario, de parámetro a número.""",
            [
                Code(
                    """from qiskit.circuit.library import n_local

two_local = n_local(3, "rx", "cz")
print(two_local.num_parameters)
bound = two_local.assign_parameters({p: 0 for p in two_local.parameters})""",
                    id="c",
                ),
                Out("12", id="o", hidden=True, check=True),
                Circ(
                    3,
                    [
                        G("rx", 0, p="θ0"),
                        G("rx", 1, p="θ1"),
                        G("rx", 2, p="θ2"),
                        G("cz", 0, 1),
                        G("cz", 0, 2),
                        G("cz", 1, 2),
                        G("rx", 0, p="θ3"),
                        G("rx", 1, p="θ4"),
                        G("rx", 2, p="θ5"),
                        G("box", 0, 2, label="…", hidden=False),
                    ],
                    id="q",
                ),
            ],
            [A("show", "o", at="ej"), A("hl", "c", at="asig", lines=[5])],
        ),
        beat(
            "datos",
            ("", "Codificar datos"),
            """Los circuitos de codificación cargan datos clásicos en estados cuánticos, para el aprendizaje automático cuántico. Hay tres estrategias.
             [[amp]]Codificación en amplitud: cada número va a la amplitud de un estado de la base. Guarda dos a la n números en n qubits, pero puede ser costosa de preparar.
             [[bas]]Codificación en base: el entero k se codifica preparando el estado k.
             [[ang]]Y codificación en ángulo: cada número es el ángulo de una rotación. En los computadores actuales se usa mucho, por ejemplo con zz feature map.""",
            [
                Table(
                    ["Codificación", "Idea", "Costo"],
                    [
                        [
                            "Amplitud",
                            "$x_k$ → amplitud de $|k\\rangle$ · $2^n$ datos en $n$ qubits",
                            "alto",
                        ],
                        ["Base", "entero $k$ → $|k\\rangle$", "bajo"],
                        ["Ángulo", "$x_k$ → ángulo de una rotación", "bajo · el más usado hoy"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                ),
                Code(
                    """from qiskit.circuit.library import zz_feature_map

features = [0.2, 0.4, 0.8]
feature_map = zz_feature_map(feature_dimension=len(features))
encoded = feature_map.assign_parameters(features)""",
                    id="c",
                    hidden=True,
                ),
            ],
            [
                A("item", "t", at="amp", i=0),
                A("item", "t", at="bas", i=1),
                A("item", "t", at="ang", i=2),
                A("show", "c", at="ang", t=2),
            ],
        ),
        beat(
            "evolucion",
            ("", "Evolución temporal"),
            """Los circuitos de evolución temporal simulan cómo cambia un estado con el tiempo, bajo un hamiltoniano. Sirven para estudiar transporte de calor o transiciones de fase, y son la base de estados de química y del algoritmo QAOA.
             [[ham]]Aquí el hamiltoniano es Z Z en los qubits cero y uno más Z Z en los qubits uno y dos. [[gate]]PauliEvolutionGate construye la puerta e elevado a menos i H t, con t igual a uno, [[comp]]y la componemos después de preparar el estado inicial.""",
            [
                Code(
                    """from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import SparsePauliOp

state = QuantumCircuit(3)
state.h(1)
hamiltonian = SparsePauliOp(["ZZI", "IZZ"])
evolution = PauliEvolutionGate(hamiltonian, time=1)
state.compose(evolution, inplace=True)""",
                    id="c",
                ),
                Row(
                    Circ(3, [G("h", 1), G("box", 0, 1, 2, label="exp(−iHt)", hidden=True)], id="q"),
                    M(r"U(t)=e^{-iHt},\quad H=Z_1Z_0+Z_2Z_1", id="m", size=36),
                    gap=30,
                ),
            ],
            [
                A("hl", "c", at="ham", lines=[6]),
                A("hl", "c", at="gate", lines=[7]),
                A("hl", "c", at="comp", lines=[8]),
                A("gate", "q", at="comp", i=1),
            ],
        ),
        beat(
            "referencia",
            ("", "Referencia y complejidad"),
            """Otros circuitos sirven para medir qué tan bien funciona el hardware, o qué tan difícil es un problema.
             [[qv]]El volumen cuántico mide con qué precisión un computador ejecuta circuitos aleatorios de cierto tipo: cuanto más grande el circuito que ejecuta bien, mayor el puntaje. Toma en cuenta todo: número de qubits, fidelidad, conectividad y software.
             [[iqp]]Los circuitos IQP, difíciles de simular clásicamente, ponen puertas diagonales entre dos capas de Hadamard. [[otros]]Y hay más: el operador de Grover y el circuito de Fourier checking.""",
            [
                Code(
                    """from qiskit.circuit.library import quantum_volume

qv = quantum_volume(4)
print(qv.count_ops())""",
                    id="c",
                ),
                Out("OrderedDict({'unitary': 8})", id="o", hidden=True, check=True),
                L(
                    [
                        "`quantum_volume`: bloques unitarios aleatorios de 2 qubits",
                        "`iqp`: H · diagonales · H",
                        "`grover_operator`, `fourier_checking`",
                    ],
                    id="l",
                    stagger=True,
                    size=27,
                ),
            ],
            [
                A("show", "o", at="qv"),
                A("item", "l", at="qv", t=2, i=0),
                A("item", "l", at="iqp", i=1),
                A("item", "l", at="otros", i=2),
            ],
        ),
        beat(
            "suma_pred",
            ("", "Antes de sumar"),
            """La biblioteca también tiene circuitos aritméticos. Vamos a sumar con un circuito: a vale dos y b vale tres, y el resultado queda en el registro de b. [[cual]]Si medimos b, ¿qué número esperas?""",
            [T("a = 2 · b = 3 · medimos el registro de b", "body", id="t")],
            ask=predict(
                "Tras sumar, ¿qué número sale al medir el registro de `b`?",
                ["2", "3", "5", "6"],
                "Anotado. Construyamos el sumador.",
            ),
        ),
        beat(
            "suma",
            ("", "Aritmética: sumar 2 + 3"),
            """Estos circuitos aritméticos son útiles en estimación de amplitud o en el algoritmo HHL. [[add]]FullAdderGate de tres suma dos números de tres bits, a y b, y deja el resultado en el registro de b.
             [[ini]]Preparamos a igual a dos y b igual a tres con initialize. [[regs]]El sumador usa además un qubit de acarreo de entrada y otro de salida.
             [[med]]Medimos el registro b. [[res]]En los mil veinticuatro disparos sale cinco.""",
            [
                Code(
                    """from qiskit.circuit.library import FullAdderGate
from qiskit import QuantumRegister, ClassicalRegister
from qiskit.primitives import StatevectorSampler

reg_a = QuantumRegister(3, "a")
number_a = QuantumCircuit(reg_a)
number_a.initialize(2)
reg_b = QuantumRegister(3, "b")
number_b = QuantumCircuit(reg_b)
number_b.initialize(3)

qregs = [QuantumRegister(1, "cin"), QuantumRegister(3, "a"),
         QuantumRegister(3, "b"), QuantumRegister(1, "cout")]
result_reg = ClassicalRegister(3, "res")
circuit = QuantumCircuit(*qregs, result_reg)
circuit = (circuit.compose(number_a, qubits=reg_a)
           .compose(number_b, qubits=reg_b)
           .compose(FullAdderGate(3)))
circuit.measure(reg_b, result_reg)

result = StatevectorSampler().run([circuit]).result()
print(result[0].data.res.get_int_counts())""",
                    id="c",
                    size=19,
                ),
                Out("{5: 1024}", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="add", range="17-19"),
                A("hl", "c", at="ini", range="5-10"),
                A("hl", "c", at="regs", range="12-15"),
                A("hl", "c", at="med", lines=[20]),
                A("hl", "c", at="res", range="22-23"),
                A("show", "o", at="res"),
            ],
        ),
        beat(
            "acarreo",
            ("", "Una suma que no cabe"),
            """Ahora una suma que no cabe en el registro. [[ej]]Seis más cinco son once, pero tres bits solo llegan hasta siete. [[cout]]El bit que falta lo deja el sumador en el qubit cout, el acarreo de salida.
             [[med]]Por eso medimos b y cout juntos, en un registro clásico de cuatro bits. [[res]]Sale once en los mil veinticuatro disparos. Si midiéramos solo b, saldría tres.""",
            [
                Code(
                    """from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import FullAdderGate
from qiskit.primitives import StatevectorSampler

cin = QuantumRegister(1, "cin")
a = QuantumRegister(3, "a")
b = QuantumRegister(3, "b")
cout = QuantumRegister(1, "cout")
res = ClassicalRegister(4, "res")
circuit = QuantumCircuit(cin, a, b, cout, res)
circuit.initialize(6, a)
circuit.initialize(5, b)
circuit.append(FullAdderGate(3), circuit.qubits)
circuit.measure([*b, *cout], res)

result = StatevectorSampler().run([circuit]).result()
print(result[0].data.res.get_int_counts())""",
                    id="c",
                    size=19,
                ),
                Out("{11: 1024}", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="ej", range="11-12"),
                A("hl", "c", at="cout", lines=[8]),
                A("hl", "c", at="med", lines=[14]),
                A("hl", "c", at="res", range="16-17"),
                A("show", "o", at="res"),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Una pregunta sobre los circuitos N-local.""",
            [Code('n_local(5, "ry", "cz", reps=2)')],
            ask=numeric(
                "¿Cuántos parámetros tiene? (una rotación por qubit en cada capa de rotaciones)",
                15,
                "Correcto: con `reps=2` hay 3 capas de rotaciones (una más que repeticiones), de 5 ángulos cada una: 15.",
                tol=0.001,
                hint="Con `reps=1` y 2 qubits había 2 capas de 2 ángulos.",
                solution=["Capas de rotación = reps + 1 = 3; 3 × 5 = 15."],
            ),
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Otra pregunta, sobre codificación.""",
            [T("Tienes 1024 números y solo 10 qubits.", "body")],
            ask=choice(
                "¿Qué codificación permitiría cargarlos todos?",
                ["en base", "en ángulo", "en amplitud"],
                2,
                "Correcto: $2^{10}=1024$ amplitudes. El precio es que preparar ese estado puede requerir un circuito muy profundo.",
                wrong=[
                    "En base, 10 qubits representan un solo entero de 10 bits.",
                    "En ángulo necesitarías una rotación por número.",
                    None,
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Primero, predice cuántos parámetros tiene un circuito N-local y compruébalo. [[n2]]Después, cambia sus argumentos para que sea más barato: ocho parámetros y solo tres puertas de dos qubits.
             [[n3]]Y por último, escribe una función que sume dos números con el sumador de la biblioteca.""",
            [
                Exercise(
                    "p2-biblioteca/parametros-nlocal",
                    '`n_local(3, "rx", "cz")` alterna capas de rotaciones RX con capas de CZ. Apuesta en `prediccion` cuántos parámetros tiene.',
                    level=1,
                    id="e1",
                    hidden=True,
                    hints=[
                        "Cada capa de rotaciones lleva un ángulo por qubit.",
                        "Por defecto `reps` vale 3, y hay una capa de rotaciones más que repeticiones.",
                        "Multiplica el número de capas de rotaciones por los ángulos de cada una.",
                    ],
                ),
                Exercise(
                    "p2-biblioteca/nlocal-barato",
                    "Cambia los argumentos de `n_local` para tener 8 parámetros y solo 3 puertas de dos qubits.",
                    level=2,
                    id="e2",
                    hidden=True,
                    hints=[
                        "Dos argumentos de `n_local` controlan el coste: uno fija cuántas veces se repite el bloque y otro, qué pares de qubits se conectan.",
                        "Los parámetros dependen solo de las repeticiones (hay una capa de rotaciones más que repeticiones); las puertas de dos qubits, de las repeticiones y de los pares conectados.",
                        "Cuenta cuántos pares de vecinos tiene una línea de 4 qubits.",
                    ],
                ),
                Exercise(
                    "p2-biblioteca/sumar",
                    "Escribe `sumar(x, y)`: `x` e `y` son enteros de 0 a 15. Devuelve un circuito con el sumador `FullAdderGate(4)` que prepara `x` en el registro `a`, `y` en el registro `b` y mide la suma completa en `res`, de 5 bits. Ojo: el sumador deja los cuatro bits bajos de la suma en `b`, no en `a`, y el quinto, el acarreo, en `cout`; sin él, `15 + 1` mediría 0. El sumador espera los qubits en el orden `cin`, `a`, `b`, `cout`.",
                    level=3,
                    id="e3",
                    hidden=True,
                    hints=[
                        "Hay tres pasos: preparar los dos números, añadir el sumador y medir los qubits donde queda la suma.",
                        "El circuito ya tiene los registros creados; el orden en que los pasas al sumador es el de `qc.qubits`.",
                        "`initialize` acepta un entero y los qubits donde escribirlo; `append` coloca una puerta sobre una lista de qubits, y `measure` acepta una lista de qubits para llenar un registro.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma. Escribe con tus palabras; lo que escribas se guarda en el navegador.""",
            [T("La biblioteca ahorra código, pero hay que saber qué hay dentro.", "subtitle")],
            ask=reflect(
                "¿Qué ganas y qué pierdes al usar un circuito de la biblioteca en vez de escribirlo puerta por puerta?",
                "Para evolucionar en el tiempo la cadena de Ising, ¿usarías `PauliEvolutionGate` o escribirías `rzz` y `rx` a mano? Defiende tu elección.",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Las puertas estándar se añaden con append. [[r2]]Los circuitos N-local y de codificación traen parámetros. [[r3]]Hay circuitos de evolución temporal y de referencia, como el volumen cuántico.
             [[r4]]Y hasta aritmética: un sumador que calcula dos más tres.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["circuit-library"],
    practice=[
        'Dibuja `n_local(3, "ry", "cx", entanglement="linear", reps=1)` y compáralo con el de la lección.',
        "Repite la suma de tres bits con 7 + 7. ¿Cuántos bits necesita el resultado y qué registro lo deja?",
    ],
)

# ------------------------------------------------------------------ 2.5 Operadores
s_cierre, a_cierre = resumen(
    [
        "`SparsePauliOp`: suma de cadenas de Pauli · el más usado para observables",
        "`Pauli`: una cadena con fase $\\{1, i, -1, -i\\}$",
        "`Operator`: matriz densa · pocos qubits · `tensor`, `expand`, `compose`, `+`",
        "`==` exige la misma fase global · `process_fidelity` la ignora",
    ]
)
operadores = lesson(
    "p2-operadores",
    "Operadores: Operator, Pauli y SparsePauliOp",
    "Las tres clases de operadores de quantum_info: cómo construirlas, combinarlas, compararlas y usarlas en circuitos.",
    [
        "construir observables con `SparsePauliOp.from_sparse_list`",
        "combinar operadores con `tensor`, `expand`, `compose` y sumas",
        "obtener la matriz de un circuito y comparar operadores",
    ],
    [
        beat(
            "intro",
            ("", "Tres clases de operadores"),
            """En Qiskit, los operadores viven en el módulo quantum info. Hay tres clases principales.
             [[spo]]SparsePauliOp representa un operador como combinación lineal de cadenas de Pauli: es la clase que más usarás para observables.
             [[p]]Pauli representa una sola cadena de Pauli, con una fase. [[op]]Y Operator guarda la matriz completa, densa: muy general, pero su memoria crece exponencialmente con los qubits.""",
            [
                Table(
                    ["Clase", "Representa", "Cuándo"],
                    [
                        ["`SparsePauliOp`", "$\\sum_k c_k P_k$", "observables · cualquier tamaño"],
                        ["`Pauli`", "una cadena $\\pm P$, $\\pm iP$", "álgebra de Pauli"],
                        ["`Operator`", "matriz densa $2^n\\times2^n$", "pocos qubits"],
                    ],
                    id="t",
                    stagger=True,
                )
            ],
            [
                A("item", "t", at="spo", i=0),
                A("item", "t", at="p", i=1),
                A("item", "t", at="op", i=2),
            ],
        ),
        beat(
            "sparse",
            ("", "SparsePauliOp"),
            """La forma más flexible de crear un SparsePauliOp es from sparse list. Recibe tripletas: la cadena de Pauli, los índices de los qubits donde actúa y el coeficiente.
             [[ej]]Aquí, Z X sobre los qubits uno y cuatro, con coeficiente uno; e Y Y sobre los qubits cero y tres, con coeficiente menos uno más i.
             [[cad]]En la salida, cada cadena tiene cinco letras, con el qubit cero a la derecha. Fíjate: la Z va al qubit uno y la X al cuatro.""",
            [
                Code(
                    """from qiskit.quantum_info import SparsePauliOp

op1 = SparsePauliOp.from_sparse_list(
    [("ZX", [1, 4], 1.0), ("YY", [0, 3], -1 + 1j)], num_qubits=5)
print(op1)""",
                    id="c",
                ),
                Out(
                    """SparsePauliOp(['XIIZI', 'IYIIY'],
              coeffs=[ 1.+0.j, -1.+1.j])""",
                    id="o",
                    hidden=True,
                    check=True,
                ),
                M(r"\texttt{XIIZI}:\ X_4\,Z_1", id="m", hidden=True, size=38),
            ],
            [
                A("hl", "c", at="ej", lines=[4]),
                A("show", "o", at="cad"),
                A("show", "m", at="cad", t=2),
            ],
        ),
        beat(
            "aritmetica",
            ("", "Aritmética de operadores"),
            """Los SparsePauliOp se suman, se multiplican por escalares, se componen y se combinan en producto tensorial.
             [[suma]]La suma junta los términos. [[esc]]El escalar multiplica los coeficientes. [[comp]]La arroba es el producto de operadores: multiplica cada par de cadenas usando el álgebra de Pauli.
             [[tens]]Y tensor forma el producto tensorial: el resultado vive en diez qubits.""",
            [
                Code(
                    """op2 = SparsePauliOp.from_sparse_list(
    [("XXZ", [0, 1, 4], 1 + 2j), ("ZZ", [1, 2], -1 + 1j)], num_qubits=5)

op1 + op2            # suma
2 * op1              # escalar
op1 @ op2            # composición
op1.tensor(op2)      # producto tensorial: 10 qubits""",
                    id="c",
                ),
                Out(
                    """op1 @ op2:
SparsePauliOp(['YIIYX', 'XIZII', 'ZYIXZ', 'IYZZY'],
              coeffs=[ 1.+2.j, -1.+1.j, -1.+3.j,  0.-2.j])""",
                    id="o",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="suma", lines=[4]),
                A("hl", "c", at="esc", lines=[5]),
                A("hl", "c", at="comp", lines=[6]),
                A("show", "o", at="comp"),
                A("hl", "c", at="tens", lines=[7]),
            ],
        ),
        beat(
            "pauli",
            ("", "Pauli"),
            """Pauli representa una sola cadena, con una fase que puede ser uno, i, menos uno o menos i. Se escribe como texto, con un prefijo opcional para la fase: i X X, por ejemplo.
             [[fase]]Internamente la fase se guarda como un entero: la potencia de menos i. Para i X X vale tres, porque menos i al cubo es i.
             [[met]]Pauli tiene métodos útiles: el adjunto, si conmuta o anticonmuta con otra, el producto con otra cadena, y su matriz.""",
            [
                Code(
                    """from qiskit.quantum_info import Pauli

p = Pauli("iXX")
print(p.phase)
print(Pauli("XY").commutes(Pauli("YX")))
print(Pauli("XI").anticommutes(Pauli("ZI")))""",
                    id="c",
                ),
                Out("3\nTrue\nTrue", id="o", hidden=True, check=True),
                M(r"(-i)^3=i", id="m", hidden=True, size=40),
            ],
            [A("show", "m", at="fase"), A("show", "o", at="met")],
        ),
        beat(
            "operator",
            ("", "Operator"),
            """Operator guarda la matriz completa. Lo puedes crear desde un arreglo de NumPy, desde un Pauli, desde una puerta, o desde un circuito completo.
             [[circ]]Esto último es muy útil: Operator de un circuito calcula su matriz unitaria sin necesidad de un simulador. Falla si hay mediciones, resets u operaciones condicionales.
             [[dims]]Además guarda las dimensiones de los subsistemas: una matriz de dos a la N por dos a la M se interpreta como un operador de M qubits de entrada y N de salida.
             [[raro]]Si la dimensión no es potencia de dos, como seis, se toma como un solo subsistema, aunque puedes indicar, por ejemplo, un qubit y un qutrit.""",
            [
                Code(
                    """import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit.circuit.library import CXGate

Operator(Pauli("XX"))
Operator(CXGate())
bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)
U = Operator(bell)
op = Operator(np.random.rand(6, 6), input_dims=[2, 3], output_dims=[2, 3])
print(U.input_dims(), op.input_dims())""",
                    id="c",
                    size=23,
                ),
                Out("(2, 2) (2, 3)", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="circ", range="8-11"),
                A("hl", "c", at="dims", lines=[13]),
                A("show", "o", at="dims"),
                A("hl", "c", at="raro", lines=[12]),
            ],
        ),
        beat(
            "combinar",
            ("", "Combinar operadores"),
            """Los Operator se combinan de varias formas, y el orden importa. [[tens]]A punto tensor de B es A producto tensorial B: B queda en el subsistema cero y A en el uno.
             [[exp]]expand hace lo mismo al revés: A expand B es B producto tensorial A.
             [[comp]]A compose B es la multiplicación de matrices, pero con B aplicado después de A: B por A. [[front]]Con front igual a True se invierte: A por B.
             [[qargs]]Y con qargs puedes componer un operador pequeño sobre algunos qubits de uno grande.""",
            [
                Table(
                    ["Código", "Resultado"],
                    [
                        ["`A.tensor(B)`", "$A\\otimes B$ ($B$ en el subsistema 0)"],
                        ["`A.expand(B)`", "$B\\otimes A$"],
                        ["`A.compose(B)`", "$B\\cdot A$ (primero $A$, después $B$)"],
                        ["`A.compose(B, front=True)`", "$A\\cdot B$"],
                        ["`op.compose(XZ, qargs=[0, 2])`", "$XZ$ sobre los qubits 0 y 2 de `op`"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                )
            ],
            [
                A("item", "t", at="tens", i=0),
                A("item", "t", at="exp", i=1),
                A("item", "t", at="comp", i=2),
                A("item", "t", at="front", i=3),
                A("item", "t", at="qargs", i=4),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Calcula con matrices de Pauli.""",
            [
                Code("""A = Operator(Pauli("Y"))
B = Operator(Pauli("X"))
A.compose(B)"""),
                M(
                    r"Y=\begin{pmatrix}0&-i\\i&0\end{pmatrix},\quad X=\begin{pmatrix}0&1\\1&0\end{pmatrix}",
                    size=36,
                ),
            ],
            ask=choice(
                "¿Qué matriz devuelve?",
                [
                    "$\\begin{pmatrix}i&0\\\\0&-i\\end{pmatrix}$",
                    "$\\begin{pmatrix}-i&0\\\\0&i\\end{pmatrix}$",
                    "$\\begin{pmatrix}0&-i\\\\i&0\\end{pmatrix}$",
                    "$\\begin{pmatrix}0&1\\\\1&0\\end{pmatrix}$",
                ],
                0,
                "Correcto: `A.compose(B)` es $B\\cdot A=XY=\\begin{pmatrix}i&0\\\\0&-i\\end{pmatrix}$.",
                wrong=[
                    None,
                    "Ese es $YX$, es decir `A.compose(B, front=True)`.",
                    "Ese es $Y$ solo.",
                    "Ese es $X$ solo.",
                ],
            ),
        ),
        beat(
            "lineal",
            ("", "Sumas y unitariedad"),
            """Los Operator también se suman y se multiplican por escalares. [[ej]]Por ejemplo, un medio de XX más YY menos tres ZZ.
             [[unit]]Pero cuidado: tensor, expand y compose conservan la unitariedad; las combinaciones lineales no. Este operador no es unitario.
             [[circ]]Los operadores unitarios se insertan en un circuito con append, como una UnitaryGate. Un Pauli también se puede añadir directamente y se convierte en puertas de Pauli.""",
            [
                Code(
                    """XX = Operator(Pauli("XX"))
YY = Operator(Pauli("YY"))
ZZ = Operator(Pauli("ZZ"))
op = 0.5 * (XX + YY - 3 * ZZ)
print(op.is_unitary())

circ = QuantumCircuit(2, 2)
circ.append(XX, [0, 1])          # se convierte en UnitaryGate
circ.append(Pauli("XX"), [0, 1])""",
                    id="c",
                ),
                Out("False", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="ej", lines=[4]),
                A("show", "o", at="unit"),
                A("hl", "c", at="circ", range="7-9"),
            ],
        ),
        beat(
            "fase_pred",
            ("", "Antes de comparar"),
            """Dos Operator se comparan con doble igual, que revisa cada elemento de la matriz. Multiplicar una puerta por e elevado a i medio es solo una fase global: físicamente es la misma operación. [[cual]]¿Qué crees que responde el doble igual?""",
            [
                Code(
                    """from qiskit.circuit.library import XGate

print(Operator(XGate()) == np.exp(0.5j) * Operator(XGate()))""",
                    id="c",
                )
            ],
            [A("hl", "c", at="cual", lines=[3])],
            ask=predict(
                "¿Qué imprime la comparación?",
                ["`True`", "`False`", "un error"],
                "Anotado. Veamos qué dice Qiskit.",
            ),
        ),
        beat(
            "comparar",
            ("", "Comparar operadores"),
            """Comparemos. [[fase]]Imprime falso: dos unitarias que solo difieren en una fase global no son iguales para doble igual, aunque físicamente sean la misma operación. Si apostaste por verdadero, pensaste como físico; el doble igual piensa como matemático.
             [[fid]]Para eso está process fidelity, una medida de qué tan parecidos son dos canales cuánticos. Para unitarias, no depende de la fase global: aquí da exactamente uno.""",
            [
                Code(
                    """from qiskit.quantum_info import process_fidelity
from qiskit.circuit.library import XGate

print(Operator(Pauli("X")) == Operator(XGate()))
print(Operator(XGate()) == np.exp(0.5j) * Operator(XGate()))
print(process_fidelity(Operator(XGate()), np.exp(0.5j) * Operator(XGate())))""",
                    id="c",
                ),
                Out("True\nFalse\n1.0", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="fase", lines=[5]),
                A("show", "o", at="fase"),
                A("hl", "c", at="fid", lines=[6]),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Una pregunta práctica.""",
            [
                T(
                    "Necesitas el hamiltoniano de una cadena de 100 espines, con términos $Z_iZ_{i+1}$ y $X_i$.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué clase usarías?",
                ["`Operator`", "`SparsePauliOp`", "`Pauli`"],
                1,
                "Correcto: guarda solo unos 200 términos. Un `Operator` necesitaría una matriz de $2^{100}\\times2^{100}$.",
                wrong=[
                    "Una matriz densa de 100 qubits no cabe en ninguna memoria.",
                    None,
                    "Un `Pauli` es una sola cadena; aquí hay una suma de muchas.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Primero, predice el resultado de componer una X y una Z en cada orden. [[n2]]Después, usa el argumento qargs para colocar un operador sobre los qubits que tú elijas.
             [[n3]]Y por último, escribe una función que construya la cadena de Heisenberg para cualquier número de espines.""",
            [
                Exercise(
                    "p2-operadores/orden-compose",
                    'Predice el resultado de `A.compose(B)` con $A=X$ y $B=Z$: escribe en `orden` `"XZ"` o `"ZX"`, según el producto de matrices que sea.',
                    level=1,
                    id="e1",
                    hidden=True,
                    hints=[
                        "Piensa en un circuito: lo que se aplica primero queda a la derecha del producto.",
                        'Imprime `resultado.data` y compáralo con `Operator(Pauli("XZ")).data` y con `Operator(Pauli("ZX")).data`.',
                        "Escribe a mano el producto de matrices que significa «primero `A`, después `B`» y busca cuál de las dos matrices impresas coincide.",
                    ],
                ),
                Exercise(
                    "p2-operadores/compose-qargs",
                    "Cambia `qargs` para colocar $XZ$ sobre los qubits 1 y 2 de un operador de 3 qubits: el resultado debe ser `ZXI`.",
                    level=2,
                    id="e2",
                    hidden=True,
                    hints=[
                        "`XZ` tiene dos qubits: $Z$ actúa en su qubit 0 y $X$ en su qubit 1.",
                        "El primer elemento de `qargs` es el qubit del operador grande donde cae el qubit 0 de `XZ`.",
                        "Mira en `ZXI` qué letra queda en cada qubit (el qubit 0 es la última) y ordena `qargs` para que cada una caiga en su sitio.",
                    ],
                ),
                Exercise(
                    "p2-operadores/heisenberg",
                    r"Escribe `heisenberg(n)`, con `n` el número de espines de la cadena (al menos 2): devuelve el `SparsePauliOp` de `n` qubits $\sum_i X_iX_{i+1}+Y_iY_{i+1}+Z_iZ_{i+1}$, con coeficiente 1 en cada término. Ojo: una cadena de `n` espines tiene `n - 1` pares de vecinos, y el operador debe tener `n` qubits.",
                    level=3,
                    id="e3",
                    hidden=True,
                    hints=[
                        "Piensa en los pares de vecinos: cada uno aporta los mismos tres términos, cada uno sobre sus dos qubits.",
                        "`from_sparse_list` recibe tripletas: la cadena de Pauli, los qubits donde actúa y el coeficiente.",
                        "Un bucle sobre los pares y otro sobre las tres cadenas llenan la lista.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma. Escribe con tus palabras; lo que escribas se guarda en el navegador.""",
            [T("Elegir la clase correcta es elegir cuánta memoria gastas.", "subtitle")],
            ask=reflect(
                "¿Por qué `A.compose(B)` es el producto $B\\cdot A$ y no $A\\cdot B$? Explícalo con lo que pasa en un circuito.",
                "Tu cadena de Ising tiene 100 espines. ¿Qué perderías si la guardaras como `Operator` en vez de `SparsePauliOp`, y qué sigues pudiendo hacer con la versión escasa?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]SparsePauliOp para observables. [[r2]]Pauli para una sola cadena con fase. [[r3]]Operator para matrices densas pequeñas, con tensor, expand, compose y sumas.
             [[r4]]Y para comparar unitarias sin importar la fase global, process fidelity.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["operators-overview", "operator-class"],
    practice=[
        "Verifica que `Operator(qc)` de un circuito H–CX–H coincide con la matriz que calculas a mano.",
        'Construye `SparsePauliOp(["XX", "YY", "ZZ"])` y comprueba con `.to_matrix()` que sus autovalores son $1, 1, 1, -3$.',
    ],
)

# ------------------------------------------------------------------ 2.6 Observables y síntesis
s_cierre, a_cierre = resumen(
    [
        "todo observable: $O=\\sum_k\\alpha_kP_k$ (coeficientes reales si es hermítico)",
        "`SparsePauliOp.from_operator(matriz)`: descomposición $\\tfrac{1}{2^n}\\mathrm{Tr}(OP)$",
        "medir $X$: H · medir $Y$: S† y H (Estimator lo hace solo)",
        "`circuit.unitary(U, qubits)` sintetiza · re-sintetizar puede acortar circuitos",
    ]
)
observables = lesson(
    "p2-observables",
    "Observables en la base de Pauli y síntesis de unitarios",
    "Escribir observables como sumas de Pauli, descomponer matrices, medir en otras bases y sintetizar matrices unitarias en puertas.",
    [
        "escribir un hamiltoniano de Ising con `from_sparse_list`",
        "descomponer una matriz en cadenas de Pauli y medir en las bases $X$ e $Y$",
        "sintetizar una unitaria y re-sintetizar un circuito para acortarlo",
    ],
    [
        beat(
            "pauli",
            ("", "Todo observable es una suma de Paulis"),
            """Un observable es una propiedad física que se puede medir: la energía de un sistema, su magnetización, las correlaciones entre espines.
             [[suma]]Para medir un observable de n qubits en un computador cuántico, hay que escribirlo como suma de productos tensoriales de matrices de Pauli.
             [[mat]]Las cuatro matrices: identidad, X, Y y Z. [[herm]]Como un observable es hermítico, los coeficientes son reales. Si no lo fuera, igual se puede descomponer, pero con coeficientes complejos.""",
            [
                M(
                    r"O=\sum_{k=1}^{K}\alpha_k P_k,\qquad P_k\in\{I,X,Y,Z\}^{\otimes n},\ \ \alpha_k\in\mathbb R",
                    size=42,
                ),
                M(
                    r"I=\begin{pmatrix}1&0\\0&1\end{pmatrix}\ X=\begin{pmatrix}0&1\\1&0\end{pmatrix}\ Y=\begin{pmatrix}0&-i\\i&0\end{pmatrix}\ Z=\begin{pmatrix}1&0\\0&-1\end{pmatrix}",
                    id="m",
                    hidden=True,
                    size=34,
                ),
                T("$O^\\dagger=O$ → coeficientes reales", "note", id="n", hidden=True),
            ],
            [A("show", "m", at="mat"), A("show", "n", at="herm")],
        ),
        beat(
            "ising_pred",
            ("", "Antes de construir el Ising"),
            """Un ejemplo clásico: espines en una línea, con interacción Z Z entre vecinos y un campo transversal en X. [[cual]]Para cuatro espines, ¿cuántos términos tendrá el hamiltoniano?""",
            [
                M(r"H=\sum_{i}Z_iZ_{i+1}-\sum_{i}X_i", id="m", size=42),
                Code(
                    """n = 4
interactions = [("ZZ", [i, i + 1], 1) for i in range(n - 1)]
field = [("X", [i], -1) for i in range(n)]
hamiltonian = SparsePauliOp.from_sparse_list(interactions + field, num_qubits=n)""",
                    id="c",
                    setup="from qiskit.quantum_info import SparsePauliOp",
                ),
            ],
            [A("hl", "c", at="cual", lines=[2, 3])],
            ask=predict(
                "¿Cuántos términos tiene `hamiltonian`?",
                ["4", "6", "7", "8"],
                "Anotado. Veamos cómo se escribe.",
            ),
        ),
        beat(
            "ising",
            ("", "Un hamiltoniano de Ising"),
            """Veamos. [[int]]Las interacciones son tripletas Z Z sobre los qubits i e i más uno, con coeficiente uno. [[campo]]El campo, X sobre cada qubit, con coeficiente menos uno.
             [[res]]Con cuatro qubits salen siete términos: tres pares de vecinos y cuatro campos. Si dijiste ocho, contaste cuatro pares, pero en una línea hay uno menos que espines. [[mag]]Y si en vez de la energía quieres la magnetización media, el observable es la suma de las Z dividida entre n.""",
            [
                M(r"H=\sum_{i}Z_iZ_{i+1}-\sum_{i}X_i", size=42),
                Code(
                    """from qiskit.quantum_info import SparsePauliOp

n = 4
interactions = [("ZZ", [i, i + 1], 1) for i in range(n - 1)]
field = [("X", [i], -1) for i in range(n)]
hamiltonian = SparsePauliOp.from_sparse_list(interactions + field, num_qubits=n)
print(hamiltonian)""",
                    id="c",
                ),
                Out(
                    """SparsePauliOp(['IIZZ', 'IZZI', 'ZZII', 'IIIX', 'IIXI', 'IXII', 'XIII'],
              coeffs=[ 1.+0.j,  1.+0.j,  1.+0.j, -1.+0.j, -1.+0.j, -1.+0.j, -1.+0.j])""",
                    id="o",
                    hidden=True,
                    check=True,
                ),
                M(r"M=\tfrac1n\sum_i Z_i", id="m", hidden=True, size=36),
            ],
            [
                A("hl", "c", at="int", lines=[4]),
                A("hl", "c", at="campo", lines=[5]),
                A("show", "o", at="res"),
                A("show", "m", at="mag"),
            ],
        ),
        beat(
            "promedio",
            ("", "Un observable de n qubits"),
            """Construyamos la magnetización media de tres espines, esta vez sobre el eje Y. [[bucle]]Es una suma de términos de un solo qubit: una tripleta por espín, con la letra de Pauli, el espín donde actúa y el coeficiente uno entre n.
             [[res]]Con tres espines, cada término pesa un tercio. [[eje]]La letra es el eje: cambiarla por X o por Z promedia las X o las Z, sin tocar nada más.""",
            [
                Code(
                    """n = 3
axis = "Y"
mean_y = SparsePauliOp.from_sparse_list(
    [(axis, [i], 1 / n) for i in range(n)], num_qubits=n)
print(mean_y)""",
                    id="c",
                    setup="from qiskit.quantum_info import SparsePauliOp",
                ),
                Out(
                    """SparsePauliOp(['IIY', 'IYI', 'YII'],
              coeffs=[0.33333333+0.j, 0.33333333+0.j, 0.33333333+0.j])""",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="bucle", range="3-4"),
                A("show", "o", at="res"),
                A("hl", "c", at="eje", lines=[2]),
            ],
        ),
        beat(
            "descomponer",
            ("", "De matriz a Paulis"),
            """¿Y si tu observable viene como matriz? Las cadenas de Pauli forman una base de las matrices hermíticas, así que siempre se puede descomponer.
             [[coef]]Cada coeficiente es la traza de O por P, dividida entre dos a la n: la traza actúa como producto interno.
             [[code]]from operator hace ese cálculo. [[res]]Esta matriz de cuatro por cuatro resulta ser menos Z en el qubit cero, más un medio de X en el qubit uno, más Y Y.""",
            [
                M(r"O=\frac{1}{2^n}\sum_{P}\mathrm{Tr}(OP)\,P", size=42),
                Code(
                    """import numpy as np

matrix = np.array([[-1, 0, 0.5, -1], [0, 1, 1, 0.5],
                   [0.5, 1, -1, 0], [-1, 0.5, 0, 1]])
observable = SparsePauliOp.from_operator(matrix)
print(observable)""",
                    id="c",
                    hidden=True,
                ),
                Out(
                    """SparsePauliOp(['IZ', 'XI', 'YY'],
              coeffs=[-1. +0.j,  0.5+0.j,  1. -0.j])""",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [A("show", "c", at="code"), A("show", "o", at="res")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Una descomposición a mano.""",
            [M(r"O=\begin{pmatrix}1&0\\0&0\end{pmatrix}", size=48)],
            ask=choice(
                "¿Cómo se escribe en la base de Pauli?",
                ["$\\tfrac12(I+Z)$", "$\\tfrac12(I-Z)$", "$I+Z$", "$\\tfrac12(X+Z)$"],
                0,
                "Correcto: $\\tfrac12\\mathrm{Tr}(OI)=\\tfrac12$ y $\\tfrac12\\mathrm{Tr}(OZ)=\\tfrac12$; los de $X$ e $Y$ son cero. Es el proyector sobre $|0\\rangle$.",
                wrong=[
                    None,
                    "Ese es el proyector sobre $|1\\rangle$.",
                    "Falta el factor $\\tfrac12$: $I+Z$ tiene un 2 en la esquina.",
                    "$\\mathrm{Tr}(OX)=0$: no hay término en $X$.",
                ],
            ),
        ),
        beat(
            "bases",
            ("", "Medir en otras bases"),
            """Medir proyecta sobre la base computacional, así que directamente solo se pueden medir observables diagonales en ella: los que tienen solo I y Z.
             [[x]]Para medir X, primero cambias de base con una Hadamard: H X H es Z. [[y]]Para medir Y, aplicas S daga y luego H.
             [[circ]]En este circuito medimos el qubit cero en la base X, el uno en la Y y el dos en la Z, que no necesita nada.
             [[est]]Si usas Estimator, estos cambios de base se hacen solos.""",
            [
                Row(M(r"X\to Z=HXH", size=38), M(r"Y\to Z=HS^\dagger YSH", size=38), gap=50),
                Circ(
                    3,
                    [
                        G("ry", 0, p="0.8"),
                        G("cx", 0, 1),
                        G("cx", 1, 2),
                        G("barrier"),
                        G("h", 0, hidden=True),
                        G("sdg", 1, hidden=True),
                        G("h", 1, hidden=True),
                        G("barrier", hidden=True),
                        G("measure", 0, c=0, hidden=True),
                        G("measure", 1, c=1, hidden=True),
                        G("measure", 2, c=2, hidden=True),
                    ],
                    clbits=3,
                    creg="meas",
                    id="q",
                    hidden=True,
                ),
                T(
                    "Estimator hace estos cambios de base automáticamente",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("show", "q", at="x"),
                A("gate", "q", at="x", i=4),
                A("gate", "q", at="y", i=[5, 6]),
                A("gate", "q", at="circ", i=[7, 8, 9, 10]),
                A("show", "n", at="est"),
            ],
        ),
        beat(
            "sintesis",
            ("", "Sintetizar una unitaria"),
            """Ahora el problema inverso: tienes una matriz unitaria y quieres un circuito que la implemente. Eso se llama síntesis.
             [[facil]]Para algunas clases de unitarias es eficiente, como las de Clifford o las que son un producto tensorial. Pero la mayoría no, y en general el costo crece exponencialmente con los qubits.
             [[unit]]Si no conoces una descomposición mejor, circuit punto unitary la añade como una puerta, y Qiskit la sintetiza al transpilar.
             [[ojo]]El aviso: los circuitos que salen suelen ser profundos, poco adecuados para hardware ruidoso.""",
            [
                Code(
                    """from qiskit import QuantumCircuit

U = 0.5 * np.array([[1, 1, 1, 1], [-1, 1, -1, 1],
                    [-1, -1, 1, 1], [-1, 1, 1, -1]])
circuit = QuantumCircuit(2)
circuit.unitary(U, circuit.qubits)""",
                    id="c",
                ),
                Box(
                    "warn",
                    "Síntesis general",
                    T(
                        "costo exponencial · circuitos profundos · si conoces una descomposición, úsala",
                        "body",
                    ),
                    id="b",
                    hidden=True,
                ),
            ],
            [A("hl", "c", at="unit", lines=[6]), A("show", "b", at="ojo")],
        ),
        beat(
            "resintesis_pred",
            ("", "Antes de re-sintetizar"),
            """La síntesis también sirve para optimizar. Este circuito usa tres puertas de dos qubits: dos CX y una CZ. [[cual]]Si calculamos su matriz y la volvemos a sintetizar, ¿cuántas puertas de dos qubits crees que quedarán?""",
            [
                Circ(
                    2,
                    [
                        G("h", 0),
                        G("cx", 0, 1),
                        G("sx", 1),
                        G("cz", 0, 1),
                        G("x", 1),
                        G("x", 0),
                        G("cx", 0, 1),
                        G("h", 0),
                    ],
                )
            ],
            ask=predict(
                "Tras re-sintetizar, ¿cuántas puertas de dos qubits tiene el circuito?",
                ["3", "2", "1", "0"],
                "Anotado. Comprobémoslo.",
            ),
        ),
        beat(
            "resintesis",
            ("", "Re-sintetizar para acortar"),
            """Comprobemos. [[op]]Calculamos su matriz con Operator, [[re]]y la volvemos a sintetizar en un circuito nuevo. [[res]]¡Resultado: una sola CX, rodeada de rotaciones de un qubit! Una matriz de dos qubits nunca necesita más de tres puertas de dos qubits, y aquí bastó una.
             [[tr]]La función transpile hace esta re-síntesis automáticamente con niveles de optimización suficientemente altos.""",
            [
                Circ(
                    2,
                    [
                        G("h", 0),
                        G("cx", 0, 1),
                        G("sx", 1),
                        G("cz", 0, 1),
                        G("x", 1),
                        G("x", 0),
                        G("cx", 0, 1),
                        G("h", 0),
                    ],
                    id="a",
                ),
                Code(
                    """from qiskit.quantum_info import Operator

U = Operator(circuit)
better = QuantumCircuit(2)
better.unitary(U, range(2))
print(circuit.count_ops(), better.decompose().count_ops())""",
                    id="c",
                    setup="from qiskit import QuantumCircuit\n\ncircuit = QuantumCircuit(2)\ncircuit.h(0)\ncircuit.cx(0, 1)\ncircuit.sx(1)\ncircuit.cz(0, 1)\ncircuit.x(1)\ncircuit.x(0)\ncircuit.cx(0, 1)\ncircuit.h(0)",
                ),
                Out(
                    "OrderedDict({'h': 2, 'cx': 2, 'x': 2, 'sx': 1, 'cz': 1}) OrderedDict({'u': 4, 'cx': 1})",
                    id="o",
                    hidden=True,
                    check=True,
                ),
                Circ(
                    2,
                    [G("u", 0), G("u", 1), G("cx", 0, 1), G("u", 0), G("u", 1)],
                    id="b",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="op", lines=[3]),
                A("hl", "c", at="re", lines=[4, 5]),
                A("show", "o", at="res"),
                A("show", "b", at="res"),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Una pregunta sobre medición.""",
            [T("Quieres medir $\\langle X_0\\rangle$ con un Sampler, sin Estimator.", "body")],
            ask=choice(
                "¿Qué puertas añades al qubit 0 antes de medirlo?",
                ["H", "S y luego H", "S† y luego H", "Ninguna: se mide directamente"],
                0,
                "Correcto: $HXH=Z$, así que la H lleva los autoestados de $X$ a los de $Z$; luego mides normalmente.",
                wrong=[
                    None,
                    "Esas puertas llevan los autoestados de $Y$ (con el signo cambiado) a los de $Z$, no los de $X$.",
                    "Esas puertas son el cambio de base de $Y$, no el de $X$.",
                    "Sin cambio de base, el Sampler mide siempre en la base $Z$.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Primero, predice cuántos términos tiene un hamiltoniano de Ising. [[n2]]Después, añade el cambio de base que permite medir Y con un Sampler.
             [[n3]]Y por último, escribe una función que construya el observable de magnetización de una cadena, en el eje que le pidas.""",
            [
                Exercise(
                    "p2-observables/terminos-ising",
                    r"Cuatro espines en línea: $H=\sum_i Z_iZ_{i+1}-\sum_i X_i$. Apuesta en `prediccion` cuántos términos tiene `hamiltoniano`.",
                    level=1,
                    id="e1",
                    hidden=True,
                    hints=[
                        "Hay un término por cada par de vecinos y otro por cada espín.",
                        "Es una línea abierta: el último espín no se une al primero.",
                        "Cuenta por separado los términos de dos espines y los de un espín, y súmalos.",
                    ],
                ),
                Exercise(
                    "p2-observables/medir-y",
                    r"Añade a `medir_en_y` el cambio de base que permite medir $Y$ con un Sampler: con $|{+i}\rangle$ el bit debe salir siempre `0`.",
                    level=2,
                    id="e2",
                    hidden=True,
                    hints=[
                        "Un Sampler solo mide en la base $Z$: antes de medir hay que llevar $Y$ a $Z$.",
                        "El cambio de base de $Y$ usa dos puertas de la lección, en un orden concreto.",
                        "Van entre la preparación del estado y `measure_all()`; la primera que escribes es la primera que se aplica.",
                    ],
                ),
                Exercise(
                    "p2-observables/magnetizacion",
                    r"Escribe `magnetizacion(n, eje=\"Z\")`: `n` es el número de espines y `eje` la letra del Pauli (`\"X\"`, `\"Y\"` o `\"Z\"`, y `\"Z\"` si no se indica). Devuelve el `SparsePauliOp` de `n` qubits $\frac1n\sum_i\sigma_i$. Ojo: es un promedio, no una suma, así que cada término lleva el coeficiente $1/n$.",
                    level=3,
                    id="e3",
                    hidden=True,
                    hints=[
                        "Es una suma de términos de un solo qubit, uno por espín, todos con la misma letra.",
                        "`from_sparse_list` recibe tripletas: la cadena de Pauli, los qubits donde actúa y el coeficiente; aquí todos los coeficientes son iguales.",
                        "Un solo bucle sobre los espines llena la lista.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma. Escribe con tus palabras; lo que escribas se guarda en el navegador.""",
            [T("Un observable es una suma; una medición es una base.", "subtitle")],
            ask=reflect(
                "¿Por qué un Sampler no puede medir $X$ directamente, y qué hace el cambio de base para solucionarlo?",
                "En el Ising, ¿puedes medir la magnetización $M_Z$ y la energía $H$ con las mismas mediciones? Razona con los términos de cada uno.",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Todo observable es una suma de cadenas de Pauli. [[r2]]from operator descompone cualquier matriz. [[r3]]Para medir X o Y hay que cambiar de base, salvo con Estimator.
             [[r4]]Y la síntesis convierte matrices en puertas, y a veces acorta circuitos.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["specify-observables-pauli", "synthesize-unitary-operators"],
    practice=[
        "Construye el Ising de 12 qubits de la guía original y calcula su valor esperado en $|0\\rangle^{\\otimes12}$ con `Statevector(...).expectation_value(H)`.",
        "Toma un circuito aleatorio de 2 qubits con `random_circuit(2, 10)` y re-sintetízalo. ¿Cuántas CX quedan como máximo? (la respuesta general es 3).",
    ],
)

# ------------------------------------------------------------------ 2.7 Control clásico
IF_CODE = """from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer.primitives import SamplerV2

qubits = QuantumRegister(1, "q")
clbits = ClassicalRegister(1, "c")
circuit = QuantumCircuit(qubits, clbits)
(q0,), (c0,) = qubits, clbits

circuit.h(q0)
circuit.measure(q0, c0)
with circuit.if_test((c0, 1)):
    circuit.x(q0)
circuit.measure(q0, c0)

print(SamplerV2().run([circuit]).result()[0].data.c.get_counts())"""
# Context of the fragments that follow: a circuit of three qubits and three bits.
CONTROL_SETUP = """from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.classical import expr

qubits = QuantumRegister(3, "q")
clbits = ClassicalRegister(3, "c")
circuit = QuantumCircuit(qubits, clbits)
(q0, q1, q2), (c0, c1, c2) = qubits, clbits"""
# Context of the classical-expressions fragment: six qubits, three measurement bits and a register.
EXPR_SETUP = """from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.classical import expr

qr = QuantumRegister(6, "qr")
mr = ClassicalRegister(3, "mr")
creg = ClassicalRegister(3, "creg")
qc = QuantumCircuit(qr, mr, creg)
temp = qc.add_var("temp", expr.lift(creg))"""
s_cierre, a_cierre = resumen(
    [
        "medir a mitad del circuito y decidir: **feedforward**",
        "`if_test` (+ `else_`) · `switch` (+ `case.DEFAULT`) · `for_loop` · `while_loop`",
        "`qiskit.circuit.classical.expr`: XOR, NOT… · `store` guarda resultados",
        "`stretch`: duraciones relativas que se resuelven al compilar",
    ]
)
control = lesson(
    "p2-control-clasico",
    "Control clásico, feedforward y stretch",
    "Circuitos dinámicos: if, switch, for y while dentro del circuito, expresiones clásicas, store y tiempos relativos con stretch.",
    [
        "usar `if_test`, `switch`, `for_loop` y `while_loop`",
        "construir expresiones clásicas con `expr` y guardarlas con `store`",
        "usar `stretch` para alinear operaciones y hacer desacoplamiento dinámico",
    ],
    [
        beat(
            "intro",
            ("", "Circuitos dinámicos"),
            """Hasta ahora los circuitos eran fijos: puertas y, al final, mediciones. Los circuitos dinámicos miden qubits a mitad de la ejecución y, según el resultado, deciden qué hacer después, dentro del propio circuito. A eso se le llama feedforward clásico.
             [[usos]]Ya se conocen usos concretos: preparar estados como GHZ o W con circuitos poco profundos, entrelazar qubits lejanos en el mismo chip, o muestrear circuitos tipo IQP.
             [[cuatro]]Qiskit ofrece cuatro construcciones, cada una como un método del circuito que se usa con la palabra with.""",
            [
                T("Circuitos dinámicos", "title"),
                Flow(
                    [
                        dict(t="medir", s="a mitad del circuito"),
                        dict(t="decidir", s="lógica clásica"),
                        dict(t="actuar", s="más puertas"),
                    ],
                    id="f",
                ),
                Table(
                    ["Construcción", "Método"],
                    [
                        ["if / else", "`if_test`"],
                        ["switch", "`switch`"],
                        ["for", "`for_loop`"],
                        ["while", "`while_loop`"],
                    ],
                    id="t",
                    stagger=True,
                    size=25,
                ),
            ],
            [
                A("item", "t", at="cuatro", i=0),
                A("item", "t", at="cuatro", t=0.5, i=1),
                A("item", "t", at="cuatro", t=1, i=2),
                A("item", "t", at="cuatro", t=1.5, i=3),
            ],
        ),
        beat(
            "if_pred",
            ("", "Antes del primer if"),
            """Primer ejemplo: una Hadamard y una medición; sale cero o uno al azar. [[if]]Si salió uno, aplicamos una X. [[med]]Y medimos otra vez. [[cual]]¿Qué crees que sale en la segunda medición?""",
            [
                Code(
                    """circuit.h(q0)
circuit.measure(q0, c0)
with circuit.if_test((c0, 1)):
    circuit.x(q0)
circuit.measure(q0, c0)""",
                    id="c",
                    setup='from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister\n\nqubits = QuantumRegister(1, "q")\nclbits = ClassicalRegister(1, "c")\ncircuit = QuantumCircuit(qubits, clbits)\n(q0,), (c0,) = qubits, clbits',
                )
            ],
            [A("hl", "c", at="if", range="3-4"), A("hl", "c", at="med", lines=[5])],
            ask=predict(
                "En la segunda medición, ¿qué resultado sale?",
                ["siempre 0", "siempre 1", "0 o 1 al azar", "depende de la primera medición"],
                "Anotado. Simulémoslo.",
            ),
        ),
        beat(
            "if",
            ("", "if"),
            """Lo ejecutamos completo. [[if]]Si la primera medición dio uno, la X devuelve el qubit a cero. Y si dio cero, no hacemos nada. [[aer]]Para simular circuitos dinámicos usamos el Sampler de Qiskit Aer.
             [[res]]El resultado final es cero con probabilidad uno: corregimos el azar con feedforward. Si apostaste por azar, olvidaste que el if actúa antes de la segunda medición.""",
            [Code(IF_CODE, id="c", size=21), Out("{'0': 1024}", id="o", hidden=True, check=True)],
            [
                A("hl", "c", at="if", range="11-12"),
                A("hl", "c", at="aer", lines=[2, 15]),
                A("show", "o", at="res"),
            ],
        ),
        beat(
            "else",
            ("", "else y condiciones sobre registros"),
            """El with de if test puede guardar un objeto, else, que abre el bloque contrario. [[ej]]Si el qubit cero midió uno, Hadamard al qubit uno; si no, una X.
             [[reg]]También se puede condicionar sobre un registro completo. Aquí, si los bits valen cero cero uno en binario, se aplica una X al tercer qubit.
             [[circ]]En el dibujo de Qiskit, la condición aparece como círculos sobre los bits clásicos: lleno para uno, vacío para cero.""",
            [
                Code(
                    """with circuit.if_test((c0, 1)) as else_:
    circuit.h(q1)
with else_:
    circuit.x(q1)

with circuit.if_test((clbits, 0b001)):
    circuit.x(q2)""",
                    id="c",
                    setup=CONTROL_SETUP,
                ),
                Circ(
                    2,
                    [
                        G("h", 0),
                        G("measure", 0, c=0),
                        dict(g="if", q=[1], label="c₀ = 1 ? H : X", inner="H", innerColor="red"),
                    ],
                    clbits=1,
                    id="q",
                ),
            ],
            [A("hl", "c", at="ej", range="1-4"), A("hl", "c", at="reg", range="6-7")],
        ),
        beat(
            "switch",
            ("", "switch"),
            """switch elige entre varios casos según el valor de un bit o de un registro. [[cases]]Cada caso se abre con case; un caso puede cubrir varios valores, como cero y tres.
             [[def]]case punto DEFAULT se ejecuta si ningún otro coincide. [[nofall]]Y a diferencia de otros lenguajes, solo se ejecuta un bloque: no hay caída al siguiente caso.""",
            [
                Code(
                    """with circuit.switch(clbits) as case:
    with case(0b000, 0b011):
        circuit.z(q2)
    with case(0b001):
        circuit.y(q2)
    with case(case.DEFAULT):
        circuit.x(q2)""",
                    id="c",
                    setup=CONTROL_SETUP,
                )
            ],
            [A("hl", "c", at="cases", range="2-3"), A("hl", "c", at="def", range="6-7")],
        ),
        beat(
            "loops_pred",
            ("", "Antes del while"),
            """while loop repite mientras se cumpla una condición. [[while]]Aquí, Hadamard a dos qubits y medir, y repetir mientras salga uno uno. [[cual]]Al terminar, ¿con qué frecuencia crees que aparecerá el resultado uno uno?""",
            [
                Code(
                    """circuit.h([q0, q1])
circuit.measure([q0, q1], [c0, c1])
with circuit.while_loop((clbits, 0b11)):
    circuit.h([q0, q1])
    circuit.measure([q0, q1], [c0, c1])""",
                    id="c",
                    setup=CONTROL_SETUP,
                )
            ],
            [A("hl", "c", at="while", range="3-5")],
            ask=predict(
                "En el resultado final, ¿con qué frecuencia aparece `11`?",
                ["cerca del 25 %", "cerca del 50 %", "nunca", "siempre"],
                "Anotado. Veamos el histograma.",
            ),
        ),
        beat(
            "loops",
            ("", "for y while"),
            """for loop repite operaciones sobre una secuencia de valores. [[for]]Cinco X sobre un qubit: como cinco es impar, termina en uno.
             [[while]]Y el while que acabamos de ver repite mientras salga uno uno. [[res]]Al final, uno uno no aparece nunca: el bucle solo termina cuando sale otra cosa. Los otros tres resultados salen con frecuencias parecidas.""",
            [
                Code(
                    """with circuit.for_loop(range(5)) as _:
    circuit.x(q0)

circuit.h([q0, q1])
circuit.measure([q0, q1], [c0, c1])
with circuit.while_loop((clbits, 0b11)):
    circuit.h([q0, q1])
    circuit.measure([q0, q1], [c0, c1])""",
                    id="c",
                    setup=CONTROL_SETUP,
                ),
                Hist(
                    [["00", 340], ["01", 330], ["10", 354], ["11", 0]],
                    id="h",
                    grow=True,
                    hidden=True,
                    h=220,
                ),
            ],
            [
                A("hl", "c", at="for", range="1-2"),
                A("hl", "c", at="while", range="4-8"),
                A("show", "h", at="res"),
                A("grow", "h", at="res"),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Piensa en el ejemplo del switch.""",
            [
                Code(
                    """circuit.h(q0)
circuit.measure(q0, c0)
with circuit.switch(c0) as case:
    with case(0):
        circuit.h(q0)
    with case(1):
        circuit.z(q0)
circuit.measure(q0, c0)""",
                    setup=CONTROL_SETUP,
                )
            ],
            ask=choice(
                "¿Qué resultado da la medición final?",
                ["siempre 0", "siempre 1", "1 con probabilidad 3/4"],
                2,
                "Correcto: con la primera medición en 0 (probabilidad $\\tfrac12$), la H deja el qubit al azar; con 1, la Z no cambia $|1\\rangle$ (solo le da una fase). $P(1)=\\tfrac12\\cdot\\tfrac12+\\tfrac12\\cdot1=\\tfrac34$.",
                wrong=[
                    "Con 1, la Z deja el qubit en $|1\\rangle$: no siempre sale 0.",
                    "Con 0, la H deja el qubit al azar: no siempre sale 1.",
                    None,
                ],
            ),
        ),
        beat(
            "expr",
            ("", "Expresiones clásicas"),
            """El módulo qiskit punto circuit punto classical permite calcular con bits durante la ejecución. [[lift]]expr punto lift convierte un bit en una expresión, [[xor]]y bit xor calcula la paridad de varios bits.
             [[ghz]]Con esto se prepara un estado GHZ de muchos qubits con un circuito poco profundo: se crean pares de Bell, se miden los qubits que los unen, y cada qubit se corrige con una X si la paridad de las mediciones anteriores es impar.
             [[store]]store guarda el resultado de una expresión para reutilizarlo: aquí guarda el NOT de un registro entero de una vez, en paralelo, en lugar de negar bit por bit dentro de la expresión.""",
            [
                Code(
                    """from qiskit.circuit.classical import expr

parity = expr.lift(mr[0])
for k in [1, 2]:
    parity = expr.bit_xor(mr[k], parity)
with qc.if_test(parity):
    qc.x(qr[5])

qc.store(temp, expr.bit_not(creg))""",
                    id="c",
                    setup=EXPR_SETUP,
                )
            ],
            [
                A("hl", "c", at="lift", lines=[3]),
                A("hl", "c", at="xor", range="4-5"),
                A("hl", "c", at="ghz", range="6-7"),
                A("hl", "c", at="store", lines=[9]),
            ],
        ),
        beat(
            "stretch",
            ("", "stretch: tiempos relativos"),
            """En hardware importan los tiempos. Desde Qiskit dos punto cero, los retrasos, delay, pueden tener una duración stretch: relativa en vez de absoluta. Su valor concreto se resuelve al compilar, cuando ya se conoce cuánto dura cada puerta calibrada.
             [[dd]]Un uso típico: mientras el qubit cero ejecuta un bloque condicional, el qubit uno espera ocioso y acumula errores. Le aplicamos desacoplamiento dinámico: retraso s, X, retraso dos s, X, retraso s.
             [[bar]]Un par de barreras marca el intervalo, y el compilador elige s para que todo llene exactamente ese tiempo.""",
            [
                Code(
                    """s = circuit.add_stretch("s")
circuit.delay(s, q1)
circuit.x(q1)
circuit.delay(expr.mul(s, 2), q1)
circuit.x(q1)
circuit.delay(s, q1)
circuit.barrier()""",
                    id="c",
                    setup=CONTROL_SETUP,
                ),
                Flow(
                    [
                        dict(t="s"),
                        dict(t="X", color="blue"),
                        dict(t="2s"),
                        dict(t="X", color="blue"),
                        dict(t="s"),
                    ],
                    id="f",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="dd", range="1-6"),
                A("show", "f", at="dd", t=2),
                A("hl", "c", at="bar", lines=[7]),
            ],
        ),
        beat(
            "resto",
            ("", "Cómo se resuelve un stretch"),
            """Un ejemplo numérico. El qubit cero espera cien unidades de tiempo; en el uno hay tres retrasos a y tres X de ocho unidades cada una.
             [[ec]]La ecuación es tres a más veinticuatro igual a cien: a vale veinticinco, con un resto de uno. [[resto]]En el servicio de IBM, el resto se suma al primer retraso que usa el stretch: veintiséis, veinticinco, veinticinco.
             [[lim]]El soporte en hardware es experimental, con límites: un stretch por conjunto de qubits entre barreras, cada stretch en una sola región entre barreras, expresiones de la forma X por stretch más Y, y nunca retrasos negativos.""",
            [
                M(r"3a+3\cdot 8=100\ \Rightarrow\ a=25,\ \text{resto }1", size=42),
                M(r"\text{retrasos: }\gold{26},\ 25,\ 25", id="m", hidden=True, size=40),
                Box(
                    "warn",
                    "Límites en IBM Quantum (experimental)",
                    L(
                        [
                            "un stretch por conjunto de qubits entre barreras",
                            "cada stretch en una sola región entre barreras",
                            "solo $X\\cdot\\text{stretch}+Y$ · nunca negativo",
                        ],
                        size=25,
                    ),
                    id="b",
                    hidden=True,
                ),
            ],
            [A("show", "m", at="resto"), A("show", "b", at="lim")],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Resuelve un stretch.""",
            [
                M(
                    r"\text{qubit 0: delay}(60)\qquad\text{qubit 1: } a,\ X,\ a,\ X,\ a,\ X,\ a",
                    size=36,
                ),
                T("cada X dura 8 unidades", "note"),
            ],
            ask=numeric(
                "¿Cuánto vale $a$ (sin contar el resto)?",
                9,
                "Correcto: $4a+24=60$, así que $a=9$ y no hay resto.",
                tol=0.001,
                hint="Cuenta cuántas veces aparece $a$ y cuántas X hay.",
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Primero, predice qué sale al corregir con if test una moneda al azar. [[n2]]Después, cambia la condición del if para que el resultado final sea siempre uno.
             [[n3]]Y por último, escribe una función que repita un experimento con while loop hasta que el bit clásico valga uno.""",
            [
                Exercise(
                    "p2-control-clasico/corregir-moneda",
                    'Predice el resultado final del circuito que corrige la moneda con `if_test`: escribe en `prediccion` `"0"`, `"1"` o `"azar"`.',
                    level=1,
                    needs="aer",
                    id="e1",
                    hidden=True,
                    hints=[
                        "La X solo se aplica en la rama en que el bit medido vale 1.",
                        "En esa rama el qubit también vale 1, porque acabas de medirlo.",
                        "Sigue cada rama por separado hasta la segunda medición y compara lo que lee en cada una.",
                    ],
                ),
                Exercise(
                    "p2-control-clasico/siempre-uno",
                    "Cambia solo la condición del `if_test` para que el resultado final sea siempre 1.",
                    level=2,
                    needs="aer",
                    id="e2",
                    hidden=True,
                    hints=[
                        "Sigue las dos ramas de la primera medición hasta la segunda: en cada una, ¿qué lee el bit al final?",
                        "No toques las puertas ni las mediciones: lo único que cambia es la condición del `if_test`.",
                        "La condición es una pareja `(bit, valor)`: el `if_test` se cumple cuando el bit medido vale ese valor.",
                    ],
                ),
                Exercise(
                    "p2-control-clasico/hasta-uno",
                    "Escribe `hasta_uno()`: devuelve un circuito de 1 qubit `q` y 1 bit `c` (ya creados) que lanza la moneda y repite con `while_loop` hasta medir 1, sin usar ninguna puerta X. Ojo: el bucle repite mientras la condición se cumple, no hasta que se cumpla, y el bit debe medirse antes de entrar en el bucle.",
                    level=3,
                    needs="aer",
                    id="e3",
                    hidden=True,
                    hints=[
                        "Piensa en un «repetir hasta»: el bucle sigue mientras el resultado todavía no es el que buscas.",
                        "Primero va una moneda fuera del bucle, para que el bit tenga un valor que comprobar; el cuerpo del bucle lanza la moneda otra vez.",
                        "La condición del bucle es una pareja `(registro, valor)`, igual que la del `if_test`.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma. Escribe con tus palabras; lo que escribas se guarda en el navegador.""",
            [T("Medir a mitad del circuito cambia lo que un circuito puede hacer.", "subtitle")],
            ask=reflect(
                "¿Qué puede hacer un circuito dinámico que uno estático no puede? Pon un ejemplo de este capítulo.",
                "Mientras la lógica clásica decide, los demás qubits esperan. ¿Qué les puede pasar, y qué herramienta del capítulo ayuda?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Un circuito dinámico mide a mitad de camino y decide. [[r2]]if test, switch, for loop y while loop, siempre con with. [[r3]]Las expresiones clásicas calculan paridades y store las guarda.
             [[r4]]Y stretch deja que el compilador fije los tiempos. En la Parte siete veremos qué de esto se puede ejecutar en el hardware de IBM.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["classical-feedforward-and-control-flow", "stretch"],
    practice=[
        "Ejecuta el ejemplo `while_loop` con `qiskit_aer.primitives.SamplerV2` y verifica que `11` nunca aparece.",
        "Construye el GHZ de 8 qubits con paridades de la guía original y compara su profundidad con el GHZ en cadena de CNOT.",
    ],
)

# ------------------------------------------------------------------ 2.8 OpenQASM y QPY
# Context of the custom-gates fragment: a program with the rzx gate and another that uses rxx without defining it.
QASM_CUSTOM_SETUP = '''program = """
OPENQASM 2.0;
include "qelib1.inc";
gate rzx(angle) a, b { h b; cx a, b; rz(angle) b; cx a, b; h b; }
qreg q[2];
rzx(0.5) q[0], q[1];
"""
old_program = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
rxx(0.5) q[0], q[1];
"""'''
s_cierre, a_cierre = resumen(
    [
        "OpenQASM: lenguaje de intercambio entre herramientas · versiones 2 y 3",
        "`qasm2.loads/load/dumps/dump` · `CustomInstruction`, `LEGACY_CUSTOM_INSTRUCTIONS`, `strict`",
        "`qasm3.dumps/dump` · importar requiere `qiskit-qasm3-import`",
        "QPY: `qpy.dump` / `qpy.load` (devuelve una lista)",
    ]
)
qasm = lesson(
    "p2-qasm",
    "OpenQASM y guardar circuitos",
    "El lenguaje OpenQASM 2 y 3, cómo importar y exportar circuitos, qué funciones admite el hardware, y cómo guardarlos con QPY.",
    [
        "leer un programa OpenQASM 3 sencillo",
        "importar y exportar circuitos con `qasm2` y `qasm3`",
        "guardar y cargar circuitos con QPY",
    ],
    [
        beat(
            "que",
            ("", "Qué es OpenQASM"),
            """[[que]]OpenQASM, el lenguaje ensamblador cuántico abierto, describe circuitos como secuencias ordenadas de operaciones con parámetros, como puertas, mediciones y resets, más cálculo clásico en tiempo real.
             [[v3]]Su versión más reciente, OpenQASM tres, añadió control de flujo con feedforward, modificadores de puertas y descripciones de pulsos.
             [[franca]]Su papel principal es ser la lengua franca entre herramientas: puedes construir un circuito con una, transpilar con otra, y pasarlo entre ellas en OpenQASM.""",
            [
                Code(
                    """OPENQASM 3;
include "stdgates.inc";
const n = 3;           // número de qubits
qubit[n] q;
bit[n] c;
h q[0];
for k in [0:n-1] {
  cnot q[k], q[k+1];
}
c = measure q;""",
                    "qasm",
                    id="c",
                    reveal=True,
                    size=26,
                )
            ],
            [
                A("lines", "c", at="que", to=5),
                A("lines", "c", at="v3", to=10),
                A("hl", "c", at="v3", range="7-9"),
            ],
        ),
        beat(
            "q2import",
            ("", "Importar OpenQASM 2"),
            """Para importar OpenQASM dos hay dos funciones: load, que lee un archivo, y loads, que recibe el programa como texto.
             [[ej]]Este programa crea un estado de Bell, y loads lo convierte en un QuantumCircuit.
             [[lib]]Qiskit trata el archivo qelib1 punto inc como la biblioteca estándar, con exactamente las puertas del artículo original de OpenQASM dos, y las representa con las puertas de su propia biblioteca.""",
            [
                Code(
                    '''import qiskit.qasm2

program = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q -> c;
"""
circuit = qiskit.qasm2.loads(program)
print(circuit.count_ops())''',
                    id="c",
                    size=23,
                ),
                Out(
                    "OrderedDict({'measure': 2, 'h': 1, 'cx': 1})", id="o", hidden=True, check=True
                ),
            ],
            [A("hl", "c", at="ej", lines=[12]), A("show", "o", at="ej", t=1)],
        ),
        beat(
            "custom",
            ("", "Puertas propias al importar"),
            """Las puertas definidas en el programa con gate se importan, por defecto, como puertas personalizadas. [[custom]]Puedes decirle al importador qué clase usar con CustomInstruction: el nombre, el número de parámetros, el número de qubits y el constructor.
             [[builtin]]Con builtin igual a True, la puerta está disponible aunque el programa no la defina: útil con plataformas que tratan sus puertas base como incorporadas.
             [[legacy]]Hay una trampa histórica: el exportador de Qiskit asume que qelib1 tiene más puertas de las que tiene, como rxx. Para releer esos archivos, pasa LEGACY CUSTOM INSTRUCTIONS.
             [[clas]]También puedes añadir funciones clásicas propias con CustomClassical, y activar el modo estricto, que sigue la especificación al pie de la letra.""",
            [
                Code(
                    """from qiskit import qasm2
from qiskit.circuit.library import RZXGate

customs = [qasm2.CustomInstruction("rzx", 1, 2, RZXGate)]
qasm2.loads(program, custom_instructions=customs)

qasm2.loads(old_program,
            custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)

import math
qasm2.loads(program,
            custom_classical=[qasm2.CustomClassical("arctan", 2, math.atan2)],
            strict=False)""",
                    id="c",
                    setup=QASM_CUSTOM_SETUP,
                    size=23,
                )
            ],
            [
                A("hl", "c", at="custom", range="4-5"),
                A("hl", "c", at="legacy", range="7-8"),
                A("hl", "c", at="clas", range="10-13"),
            ],
        ),
        beat(
            "export_pred",
            ("", "Antes de exportar"),
            """Aquí tienes un estado de Bell escrito en OpenQASM dos. [[med]]La medición se escribe con una flecha, de q a meas. Vamos a exportar el mismo circuito a OpenQASM tres. [[cual]]¿Cómo crees que se escribirá la medición del primer qubit?""",
            [
                Code(
                    """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg meas[2];
h q[0];
cx q[0], q[1];
measure q[0] -> meas[0];
measure q[1] -> meas[1];""",
                    "qasm",
                    id="c",
                    size=26,
                )
            ],
            [A("hl", "c", at="med", range="7-8")],
            ask=predict(
                "En OpenQASM 3, ¿cómo se escribe la medición del primer qubit?",
                [
                    "`measure q[0] -> meas[0];`",
                    "`meas[0] = measure q[0];`",
                    "`q[0].measure(meas[0]);`",
                    "`measure(q[0], meas[0]);`",
                ],
                "Anotado. Exportemos el circuito.",
            ),
        ),
        beat(
            "export",
            ("", "Exportar"),
            """Para exportar, qasm2 punto dumps devuelve el texto y dump lo escribe en un archivo. [[q3]]Lo mismo con qasm3. Fíjate en las diferencias: en OpenQASM tres, los registros se declaran con qubit y bit, y la medición se escribe como una asignación: el bit recibe el resultado de measure. La flecha desaparece.""",
            [
                Code(
                    """from qiskit import QuantumCircuit, qasm3

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()
print(qasm3.dumps(qc))""",
                    id="c",
                ),
                Out(
                    """OPENQASM 3.0;
include "stdgates.inc";
bit[2] meas;
qubit[2] q;
h q[0];
cx q[0], q[1];
barrier q[0], q[1];
meas[0] = measure q[0];
meas[1] = measure q[1];""",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [A("show", "o", at="q3")],
        ),
        beat(
            "q3import",
            ("", "Importar OpenQASM 3"),
            """Para importar OpenQASM tres hace falta un paquete extra, qiskit qasm3 import. Esta parte aún está en fase exploratoria y puede cambiar.
             [[fun]]Las funciones son las mismas: load y loads. [[cap]]El importador entiende entradas, alias con let, puertas propias con modificadores como ctrl o inv, bucles while e if.""",
            [
                Sh("$ pip install qiskit-qasm3-import", id="s"),
                Code(
                    '''import qiskit.qasm3

circuit = qiskit.qasm3.loads("""
OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
bit[2] c;
h q[0];
cx q[0], q[1];
c = measure q;
""")
print(circuit.num_qubits, circuit.num_clbits)''',
                    id="c",
                    hidden=True,
                ),
                Out("2 2", id="o", hidden=True, check=True),
            ],
            [A("show", "c", at="fun"), A("show", "o", at="cap")],
        ),
        beat(
            "tabla",
            ("", "¿Qué funciona dónde?"),
            """La tabla de funciones de OpenQASM tres distingue dos cosas: si el SDK puede representarla, y si el servicio de IBM puede ejecutarla en hardware.
             [[si]]Funciona en ambos: comentarios, bits, barreras, delay, la U incorporada, reset, measure, if y else.
             [[sdk]]Solo en el SDK: while, else if, box, los modificadores de puertas y gphase. Las puertas propias y los modificadores se resuelven al transpilar al ISA del backend.
             [[ibm]]Y lo contrario: los tipos int, uint o bool, que el importador aún no lee, sí se ejecutan en hardware si los construyes desde Python.
             [[anid]]Ojo: el control de flujo anidado, como un if dentro de otro, no se puede ejecutar en hardware.""",
            [
                Table(
                    ["Función", "SDK", "IBM QPU"],
                    [
                        [
                            "comentarios, `bit`, `barrier`, `delay`, `U`, `reset`, `measure`",
                            "✅",
                            "✅",
                        ],
                        ["`if` / `else`", "✅", "✅"],
                        ["`while`, `else if`, `box`, `ctrl @`, `inv @`, `gphase`", "✅ / 🟡", "❌"],
                        ["`for`", "🟡", "❌"],
                        ["`int`, `uint`, `bool`, comparaciones", "🟡 / ❌", "✅"],
                        ["`stretch`", "🟡", "🟡"],
                    ],
                    id="t",
                    stagger=True,
                    size=22,
                )
            ],
            [
                A("item", "t", at="si", i=0),
                A("item", "t", at="si", t=1, i=1),
                A("item", "t", at="sdk", i=2),
                A("item", "t", at="sdk", t=1, i=3),
                A("item", "t", at="ibm", i=4),
                A("item", "t", at="anid", i=5),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Una pregunta sobre la tabla.""",
            [T("Tu circuito tiene un `if` dentro de otro `if`.", "body")],
            ask=choice(
                "¿Se puede ejecutar en el hardware de IBM?",
                [
                    "sí, siempre",
                    "no: el control de flujo anidado no es ejecutable",
                    "solo si lo exportas a OpenQASM 2",
                ],
                1,
                "Correcto: el control de flujo anidado (incluido `else if`) se puede representar en Qiskit, pero no ejecutar en hardware.",
                wrong=[
                    "El hardware no admite anidamiento.",
                    None,
                    "OpenQASM 2 ni siquiera tiene bloques `if` con cuerpo.",
                ],
            ),
        ),
        beat(
            "qpy_pred",
            ("", "Antes de guardar con QPY"),
            """Para guardar un circuito exactamente como es, con todos sus objetos de Qiskit, usa QPY, el formato binario de serialización. [[dump]]qpy punto dump escribe un circuito en un archivo abierto en modo binario. [[load]]Y qpy punto load lo lee de vuelta. ¿Qué crees que devuelve?""",
            [
                Code(
                    """from qiskit import qpy

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

with open("test.qpy", "wb") as file:
    qpy.dump(qc, file)

with open("test.qpy", "rb") as handle:
    circuits = qpy.load(handle)""",
                    id="c",
                    size=23,
                    setup="from qiskit import QuantumCircuit",
                )
            ],
            [A("hl", "c", at="dump", range="8-9"), A("hl", "c", at="load", range="11-12")],
            ask=predict(
                "¿Qué es `circuits`?",
                [
                    "el circuito",
                    "una lista con el circuito",
                    "un diccionario",
                    "un texto en OpenQASM",
                ],
                "Anotado. Veamos qué devuelve.",
            ),
        ),
        beat(
            "qpy",
            ("", "Guardar circuitos con QPY"),
            """Comprobemos. [[comp]]Un archivo QPY se podrá leer con versiones más nuevas de Qiskit, aunque no necesariamente con versiones más viejas.
             [[dump]]qpy punto dump escribe uno o varios circuitos en un archivo abierto en modo binario. [[load]]Y qpy punto load los lee. Siempre devuelve una lista, aunque hayas guardado uno solo; por eso hay que tomar el elemento cero.""",
            [
                Code(
                    """from qiskit import qpy

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

with open("test.qpy", "wb") as file:
    qpy.dump(qc, file)

with open("test.qpy", "rb") as handle:
    circuits = qpy.load(handle)
print(len(circuits), circuits[0] == qc)""",
                    id="c",
                    size=23,
                ),
                Out("1 True", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="dump", range="8-9"),
                A("hl", "c", at="load", range="11-13"),
                A("show", "o", at="load", t=1.5),
            ],
        ),
        beat(
            "qpy_memoria",
            ("", "QPY sin archivo"),
            """No siempre quieres un archivo en el disco: a veces los bytes van a una base de datos o a una red. [[buf]]io punto BytesIO es un archivo que vive en la memoria, y dump lo acepta como cualquier otro. [[bytes]]Con get value sacas los bytes que escribió.
             [[load]]Para leer, envuelves esos bytes en otro BytesIO y se lo das a load. [[lista]]La respuesta sigue siendo una lista.""",
            [
                Code(
                    """import io

buffer = io.BytesIO()
qpy.dump(qc, buffer)
data = buffer.getvalue()
print(type(data).__name__, len(data) > 0)

restored = qpy.load(io.BytesIO(data))
print(type(restored).__name__, restored[0] == qc)""",
                    id="c",
                    size=23,
                ),
                Out("bytes True\nlist True", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="buf", lines=[3, 4]),
                A("hl", "c", at="bytes", lines=[5]),
                A("hl", "c", at="load", lines=[8]),
                A("show", "o", at="lista"),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Una pregunta sobre formatos.""",
            [
                T(
                    "Quieres guardar un circuito con parámetros y control de flujo para seguir trabajando mañana con Qiskit.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué formato conserva todo con más fidelidad?",
                ["OpenQASM 2", "OpenQASM 3", "QPY"],
                2,
                "Correcto: QPY guarda el objeto de Qiskit completo. OpenQASM es ideal para intercambiar con otras herramientas, pero no todo se ida y vuelve igual.",
                wrong=[
                    "OpenQASM 2 no tiene control de flujo con bloques.",
                    "OpenQASM 3 es bueno para intercambiar, pero la importación aún es parcial.",
                    None,
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Primero, predice cuántas instrucciones tiene un programa OpenQASM al importarlo. [[n2]]Después, relee un archivo antiguo que usa la puerta r x x, con las instrucciones heredadas.
             [[n3]]Y por último, escribe dos funciones, una que guarde un circuito con QPY y otra que lo cargue de vuelta.""",
            [
                Exercise(
                    "p2-qasm/instrucciones-qasm",
                    "Este programa OpenQASM 2 crea un estado de Bell y lo mide. Apuesta en `prediccion` cuántas instrucciones tiene el circuito que sale de importarlo.",
                    level=1,
                    id="e1",
                    hidden=True,
                    hints=[
                        "Cuenta la `h`, la `cx` y las mediciones.",
                        "`measure q -> c` mide un registro entero.",
                        "Fíjate en cuántas mediciones produce la sola línea `measure q -> c`.",
                    ],
                ),
                Exercise(
                    "p2-qasm/qasm-antiguo",
                    "Relee el programa que usa `rxx` pasando a `qasm2.loads` el argumento que lo reconoce.",
                    level=2,
                    id="e2",
                    hidden=True,
                    hints=[
                        "El exportador antiguo supone que `qelib1.inc` trae `rxx`, pero no la trae.",
                        "`qasm2.loads` tiene un argumento `custom_instructions` para declarar las puertas que el programa no define.",
                        "El propio módulo `qasm2` trae ya hecha la lista de puertas de los exportadores antiguos; búscala con `dir(qasm2)`.",
                    ],
                ),
                Exercise(
                    "p2-qasm/qpy",
                    "Escribe dos funciones, sin tocar el disco. `guardar(circuito)` recibe un `QuantumCircuit` y devuelve los `bytes` de su archivo QPY. `cargar(datos)` recibe esos `bytes` y devuelve el `QuantumCircuit` que contienen. Ojo: `qpy.load` devuelve una lista de circuitos, no un circuito.",
                    level=3,
                    id="e3",
                    hidden=True,
                    hints=[
                        "`qpy.dump` y `qpy.load` trabajan con archivos; necesitas un archivo que viva en memoria.",
                        "El módulo `io` trae un archivo en memoria de bytes; de él puedes sacar los bytes, y a él puedes darle los bytes.",
                        "Un archivo QPY puede contener varios circuitos; decide cuál devuelves.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar con calma. Escribe con tus palabras; lo que escribas se guarda en el navegador.""",
            [T("El formato correcto depende de quién va a leer el archivo.", "subtitle")],
            ask=reflect(
                "¿Cuándo elegirías OpenQASM y cuándo QPY para guardar un circuito? Responde según quién lo va a leer.",
                "Quieres guardar el circuito de Trotter de tu proyecto para usarlo en el hito V. ¿Qué formato usarías, y qué podría salir mal si eliges el otro?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]OpenQASM es la lengua franca entre herramientas. [[r2]]qasm2 importa y exporta, con opciones para puertas propias y archivos antiguos. [[r3]]qasm3 exporta, y para importar necesita un paquete extra.
             [[r4]]Y para guardar circuitos tal cual, QPY.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "introduction-to-qasm",
        "interoperate-qiskit-qasm2",
        "interoperate-qiskit-qasm3",
        "qasm-feature-table",
        "save-circuits",
    ],
    practice=[
        "Exporta a OpenQASM 3 un circuito con `if_test` y lee cómo queda el bloque `if`.",
        "Copia el programa OpenQASM 3 de la guía original (con `input`, `let` y `while`) y cárgalo con `qasm3.loads`.",
    ],
)

# ------------------------------------------------------------------ 2.9 Visualizar
# Context of the plot_histogram fragment: two Sampler results with the meas register.
HIST_SETUP = """from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
from qiskit.visualization import plot_histogram

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()
result = StatevectorSampler().run([qc], shots=1024).result()
second_result = StatevectorSampler().run([qc], shots=1024).result()"""
s_cierre, a_cierre = resumen(
    [
        "`draw()`: texto · `mpl` · `latex` · `filename`, `reverse_bits`, `plot_barriers`, `fold`, `style`, `scale`",
        "estados: city · hinton · paulivec · qsphere · bloch · `latex`",
        "`plot_histogram(counts, legend, sort, number_to_keep…)` · Estimator con `plt.bar`",
        "`timeline.draw(isa, target=…)`: tiempos y qubits ociosos",
    ]
)
visualizar = lesson(
    "p2-visualizar",
    "Visualizar circuitos, estados y resultados",
    "Dibujar circuitos, graficar estados (city, hinton, Pauli, q-esfera, Bloch), histogramas, valores esperados y líneas de tiempo.",
    [
        "dibujar circuitos con texto, matplotlib o LaTeX y personalizar el dibujo",
        "elegir la gráfica adecuada para un estado cuántico",
        "graficar resultados de Sampler y de Estimator",
    ],
    [
        beat(
            "draw",
            ("", "Dibujar un circuito"),
            """Para ver un circuito puedes imprimirlo o llamar a draw. Por defecto, los dos producen un dibujo en texto.
             [[dif]]La diferencia: print imprime y devuelve None; draw devuelve el dibujo sin imprimir nada. En un cuaderno parecen iguales porque Jupyter muestra el valor de la última línea.
             [[out]]Hay otros dos dibujantes: matplotlib, con output igual a mpl, y LaTeX, que necesita el paquete qcircuit. [[save]]Y con filename guardas el dibujo en un archivo, útil para circuitos grandes.""",
            [
                Code(
                    """from qiskit import QuantumCircuit

circuit = QuantumCircuit(3, 3)
circuit.x(1)
circuit.h(range(3))
circuit.cx(0, 1)
circuit.measure(range(3), range(3))
print(circuit)""",
                    id="c",
                ),
                Out(
                    """     ┌───┐          ┌─┐
q_0: ┤ H ├───────■──┤M├───
     ├───┤┌───┐┌─┴─┐└╥┘┌─┐
q_1: ┤ X ├┤ H ├┤ X ├─╫─┤M├
     ├───┤└┬─┬┘└───┘ ║ └╥┘
q_2: ┤ H ├─┤M├───────╫──╫─
     └───┘ └╥┘       ║  ║
c: 3/═══════╩════════╩══╩═
            2        0  1""",
                    id="o",
                    size=22,
                ),
                Code(
                    """circuit.draw(output="mpl", filename="circuit-mpl.jpeg")""",
                    id="c2",
                    hidden=True,
                ),
            ],
            [A("hl", "c", at="dif", lines=[8]), A("show", "c2", at="save")],
        ),
        beat(
            "opciones",
            ("", "Personalizar el dibujo"),
            """draw tiene muchas opciones. [[comunes]]Dos sirven en los tres dibujantes: reverse bits invierte el orden de los qubits y plot barriers en False oculta las barreras.
             [[fold]]fold fija el ancho máximo: en texto son caracteres por línea; en matplotlib, capas antes de partir el dibujo. [[style]]style cambia colores, solo en matplotlib, [[scale]]y scale cambia el tamaño en matplotlib y LaTeX.
             [[func]]También existe la función circuit drawer, que hace lo mismo pero recibe el circuito como argumento.""",
            [
                Table(
                    ["Opción", "Efecto", "Dibujantes"],
                    [
                        ["`reverse_bits=True`", "qubit 0 abajo", "todos"],
                        ["`plot_barriers=False`", "ocultar barreras", "todos"],
                        ["`fold=40`", "ancho máximo", "text, mpl"],
                        ["`style={…}`", "colores", "mpl"],
                        ["`scale=0.5`", "tamaño", "mpl, latex"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                ),
                Code(
                    'circuit_drawer(circuit, output="mpl", plot_barriers=False)',
                    id="c",
                    hidden=True,
                    setup="from qiskit.visualization import circuit_drawer",
                ),
            ],
            [
                A("item", "t", at="comunes", i=0),
                A("item", "t", at="comunes", t=1.5, i=1),
                A("item", "t", at="fold", i=2),
                A("item", "t", at="style", i=3),
                A("item", "t", at="scale", i=4),
                A("show", "c", at="func"),
            ],
        ),
        beat(
            "estados",
            ("", "Graficar estados"),
            """Para aprender o depurar ayuda ver el estado del computador, aunque solo es posible para sistemas pequeños.
             [[dens]]Un estado puede ser un vector de estado, o una matriz de densidad, más general, que también describe mezclas.
             [[ej]]Tomemos este estado de dos qubits: una Hadamard y una RX controlada de pi medios. [[latex]]Lo más simple es dibujarlo en LaTeX, en notación de ket.""",
            [
                Row(
                    Circ(
                        2,
                        [G("h", 0), dict(g="c", ctrl=[0], q=[1], base="rx", label="RX", p="π/2")],
                        id="q",
                    ),
                    M(
                        r"\rho=|\psi\rangle\langle\psi|\quad\text{o}\quad\rho=\sum_k p_k|\psi_k\rangle\langle\psi_k|",
                        size=34,
                    ),
                    gap=36,
                ),
                Code(
                    """from math import pi
from qiskit.quantum_info import Statevector

qc = QuantumCircuit(2)
qc.h(0)
qc.crx(pi / 2, 0, 1)
psi = Statevector(qc)
psi.draw("latex")""",
                    id="c",
                    hidden=True,
                ),
                M(
                    r"|\psi\rangle=\tfrac{\sqrt2}{2}|00\rangle+\tfrac12|01\rangle-\tfrac{i}{2}|11\rangle",
                    id="m",
                    hidden=True,
                    size=40,
                ),
            ],
            [A("show", "c", at="ej"), A("show", "m", at="latex")],
        ),
        beat(
            "graficas",
            ("", "Cinco gráficas"),
            """Qiskit tiene cinco gráficas de estados. [[city]]plot state city: la parte real e imaginaria de cada elemento de la matriz de densidad, como barras en tres dimensiones que parecen rascacielos.
             [[hinton]]plot state hinton: lo mismo, pero el tamaño de un cuadrado indica la magnitud, blanco si es positivo y negro si es negativo.
             [[pauli]]plot state paulivec: los valores esperados de cada cadena de Pauli; toda matriz de densidad es una suma de Paulis con esos pesos.
             [[qs]]plot state qsphere: la q-esfera que ya conoces de Composer. [[bloch]]Y plot bloch multivector: una esfera de Bloch por qubit, que no puede mostrar correlaciones.""",
            [
                Table(
                    ["Función", "Muestra"],
                    [
                        ["`plot_state_city`", "Re e Im de $\\rho_{ij}$ en barras 3D"],
                        ["`plot_state_hinton`", "magnitud = tamaño · signo = blanco/negro"],
                        ["`plot_state_paulivec`", "$\\langle P\\rangle$ de cada cadena de Pauli"],
                        ["`plot_state_qsphere`", "amplitud y fase sobre una esfera"],
                        [
                            "`plot_bloch_multivector`",
                            "una esfera de Bloch por qubit (sin correlaciones)",
                        ],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                ),
                T(
                    'también: `psi.draw("city")`, `"hinton"`, `"paulivec"`, `"qsphere"`, `"bloch"` · `.savefig("out.png")`',
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("item", "t", at="city", i=0),
                A("item", "t", at="hinton", i=1),
                A("item", "t", at="pauli", i=2),
                A("item", "t", at="qs", i=3),
                A("item", "t", at="bloch", i=4),
                A("show", "n", at="bloch", t=2),
            ],
        ),
        beat(
            "paulivec",
            ("", "El estado como suma de Paulis"),
            """La gráfica de Pauli tiene una versión numérica. SparsePauliOp from operator, aplicado al estado, da su matriz de densidad como suma de Paulis.
             [[coef]]Cada coeficiente es el valor esperado de esa cadena, dividido entre cuatro: por ejemplo, ZZ vale un octavo, así que su valor esperado es un medio.""",
            [
                Code(
                    """from qiskit.quantum_info import SparsePauliOp
print(SparsePauliOp.from_operator(psi))""",
                    id="c",
                ),
                Out(
                    """SparsePauliOp(['II', 'IX', 'XY', 'YI', 'YX', 'YZ', 'ZI', 'ZX', 'ZZ'],
              coeffs=[ 0.25     +0.j,  0.1767767+0.j, -0.1767767+0.j, -0.125    +0.j,
 -0.1767767+0.j,  0.125    +0.j,  0.125    +0.j,  0.1767767+0.j,
  0.125    +0.j])""",
                    id="o",
                    hidden=True,
                    check=True,
                    size=20,
                ),
                M(
                    r"|\psi\rangle\langle\psi|=\tfrac14\sum_P\langle P\rangle\,P",
                    id="m",
                    hidden=True,
                    size=38,
                ),
            ],
            [A("show", "o", at="coef"), A("show", "m", at="coef", t=2)],
        ),
        beat(
            "bloch_pred",
            ("", "Antes de la esfera de Bloch"),
            """Una apuesta con el estado de Bell, el más entrelazado de dos qubits. [[cual]]Si lo dibujamos con plot bloch multivector, que muestra una esfera por qubit, ¿qué esperas ver?""",
            [Circ(2, [G("h", 0), G("cx", 0, 1)], id="q")],
            ask=predict(
                "Para el estado de Bell, ¿qué muestra `plot_bloch_multivector`?",
                [
                    "dos flechas apuntando hacia arriba",
                    "dos flechas en el ecuador, una opuesta a la otra",
                    "dos vectores de longitud cero",
                    "una sola esfera con una flecha",
                ],
                "Anotado. Veamos qué dibuja.",
            ),
        ),
        beat(
            "bloch_res",
            ("", "Sin correlaciones"),
            """Dos esferas con vectores de longitud cero. [[cero]]Cada qubit, mirado por separado, está completamente indeterminado: sus valores esperados de X, Y y Z valen cero. [[corr]]Toda la información está en la correlación entre los dos, y la esfera de Bloch no puede mostrarla. Para eso sirven la ciudad, paulivec o la q-esfera.""",
            [
                Code(
                    """bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)
plot_bloch_multivector(Statevector(bell))""",
                    id="c",
                    setup="from qiskit import QuantumCircuit\nfrom qiskit.quantum_info import Statevector\nfrom qiskit.visualization import plot_bloch_multivector",
                ),
                Row(
                    Box(
                        "warn",
                        "Cada qubit",
                        T("$\\langle X\\rangle=\\langle Y\\rangle=\\langle Z\\rangle=0$", "body"),
                        id="a",
                        hidden=True,
                    ),
                    Box(
                        "def",
                        "Los dos juntos",
                        T("$\\langle ZZ\\rangle=\\langle XX\\rangle=1$", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=24,
                ),
            ],
            [A("show", "a", at="cero"), A("show", "b", at="corr")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Elige la gráfica.""",
            [T("Quieres ver si dos qubits están correlacionados.", "body")],
            ask=choice(
                "¿Qué gráfica **no** te sirve?",
                [
                    "`plot_state_city`",
                    "`plot_state_paulivec`",
                    "`plot_bloch_multivector`",
                    "`plot_state_qsphere`",
                ],
                2,
                "Correcto: las esferas de Bloch muestran cada qubit por separado. Un estado de Bell aparece como dos vectores de longitud cero: no se ve la correlación.",
                wrong=[
                    "La matriz de densidad completa sí contiene las correlaciones.",
                    "Los términos como $\\langle ZZ\\rangle$ muestran correlaciones.",
                    None,
                    "La q-esfera muestra el estado completo de varios qubits.",
                ],
            ),
        ),
        beat(
            "hist",
            ("", "Histogramas de Sampler"),
            """Para los resultados de Sampler, plot histogram. [[opts]]Sus opciones: legend para nombrar varias ejecuciones en la misma gráfica, sort para ordenar ascendente o descendente, number to keep para quedarte con los más frecuentes y juntar el resto,
             color, bar labels para mostrar o no los números, y figsize para el tamaño.
             [[fuera]]Como todas estas funciones devuelven una figura de matplotlib, fuera de Jupyter usa show o savefig.""",
            [
                Code(
                    """plot_histogram(
    [result[0].data.meas.get_counts(),
     second_result[0].data.meas.get_counts()],
    legend=["first", "second"],
    sort="desc",
    number_to_keep=4,
    color=["orange", "black"],
    bar_labels=False,
    figsize=(15, 12),
)""",
                    id="c",
                    setup=HIST_SETUP,
                ),
                T(
                    'fuera de Jupyter: `fig.show()` o `fig.savefig("out.png")`',
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [A("hl", "c", at="opts", range="4-9"), A("show", "n", at="fuera")],
        ),
        beat(
            "estimator",
            ("", "Graficar valores esperados"),
            """Para Estimator no hay una función propia: se usa un gráfico de barras de matplotlib. [[ej]]Aquí se estiman siete observables sobre un estado. [[bc]]Para pedirlos en una sola llamada, el arreglo de observables tiene forma siete por uno; lo verás en detalle con las primitivas.
             [[bar]]Las barras son los valores esperados, [[err]]y con yerr se añaden las barras de error, el error estándar que Estimator devuelve en stds.""",
            [
                Code(
                    """import numpy as np
from matplotlib import pyplot as plt
from qiskit.primitives import StatevectorEstimator

qc = QuantumCircuit(2)
qc.h(0)
qc.crx(1.5, 0, 1)
labels = ["ZZ", "XX", "YZ", "ZY", "XY", "XZ", "ZX"]
obs = np.fromiter([SparsePauliOp(l) for l in labels], dtype=object).reshape(7, 1)
res = StatevectorEstimator().run([(qc, obs)]).result()[0]
plt.bar(labels, res.data.evs.flatten(), yerr=res.data.stds.flatten())
print(res.data.evs.flatten().round(2))""",
                    id="c",
                    size=22,
                ),
                Hist(
                    [
                        ["ZZ", 0.46],
                        ["XX", 0],
                        ["YZ", 0.5],
                        ["ZY", 0],
                        ["XY", -0.68],
                        ["XZ", 0],
                        ["ZX", 0.73],
                    ],
                    id="h",
                    hidden=True,
                    h=170,
                    w=700,
                    digits=2,
                    color="teal",
                ),
            ],
            [
                A("hl", "c", at="ej", range="5-8"),
                A("hl", "c", at="bc", lines=[9]),
                A("hl", "c", at="bar", range="10-11"),
                A("show", "h", at="bar"),
                A("hl", "c", at="err", lines=[11]),
            ],
        ),
        beat(
            "timeline",
            ("", "Línea de tiempo"),
            """Por último, puedes ver cuándo ocurre cada operación de un circuito ya transpilado con timeline draw. Sirve para encontrar qubits ociosos, que acumulan errores.
             [[back]]Necesita el target del backend, que sabe cuánto dura cada puerta; aquí usamos un backend genérico de cinco qubits. [[style]]Hay hojas de estilo, como IQXDebugging, pensada para depurar.
             [[din]]Para circuitos dinámicos en hardware de IBM este dibujo no es exacto; para ellos existe otra herramienta, que veremos en la Parte siete.""",
            [
                Code(
                    """from qiskit.visualization.timeline import draw, IQXDebugging
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import generate_preset_pass_manager

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
backend = GenericBackendV2(5)
pm = generate_preset_pass_manager(backend=backend, optimization_level=1, scheduling_method="alap")
isa_circuit = pm.run(qc)
draw(isa_circuit, style=IQXDebugging(), target=backend.target)""",
                    id="c",
                    size=22,
                )
            ],
            [A("hl", "c", at="back", range="8-10"), A("hl", "c", at="style", lines=[11])],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Una pregunta sobre draw.""",
            [Code("circuit.draw(fold=40)")],
            ask=choice(
                "¿Qué cambia?",
                [
                    "el circuito: se descartan las puertas a partir de la 40",
                    "solo el dibujo: el ancho máximo de línea",
                    "los conteos: se simulan 40 disparos",
                ],
                1,
                "Correcto: `fold` solo cambia el dibujo; en texto son los caracteres por línea. El circuito no cambia.",
                wrong=[
                    "`draw` nunca modifica el circuito.",
                    None,
                    "Los disparos los fija el Sampler, no el dibujo.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. [[n1]]Primero, predice la probabilidad de medir cero cero en el estado de la lección y compruébala con sus probabilidades. [[n2]]Después, personaliza un dibujo de texto: el qubit cero abajo y sin barreras.
             [[n3]]Y por último, escribe una función que grafique con barras los valores esperados que calcula un Estimator.""",
            [
                Exercise(
                    "p2-visualizar/probabilidad-00",
                    r"El estado de la lección es una Hadamard y una RX controlada de $\pi/2$. Apuesta en `prediccion` la probabilidad de medir `00`.",
                    level=1,
                    id="e1",
                    hidden=True,
                    hints=[
                        "Mira primero qué hace la `H` sobre el qubit 0.",
                        "Si el qubit 0 vale 0, la RX controlada no actúa.",
                        "Suma solo las ramas que terminan en `00`; las demás no cuentan.",
                    ],
                ),
                Exercise(
                    "p2-visualizar/dibujo-texto",
                    "Dibuja el circuito en texto con el qubit 0 abajo y sin barreras: añade a `draw` las dos opciones que lo consiguen.",
                    level=2,
                    id="e2",
                    hidden=True,
                    hints=[
                        "`draw` tiene una opción que invierte el orden de los qubits y otra que decide si se dibujan las barreras.",
                        "La lección tiene una tabla con las opciones comunes de `draw`; busca ahí las dos que sirven.",
                        "Se pasan por nombre, después del formato; fíjate en el valor que debe tomar cada una.",
                    ],
                ),
                Exercise(
                    "p2-visualizar/barras-esperados",
                    'Completa dos funciones. `valores_esperados(circuito, etiquetas)` recibe un circuito sin mediciones y una lista de etiquetas de Pauli, como `["ZZ", "XX"]`, y devuelve un arreglo con el valor esperado de cada una, calculado con un `StatevectorEstimator`. `graficar(circuito, etiquetas)` dibuja en `ejes` una barra por etiqueta con esos valores. Ojo: pide todos los observables en una sola llamada a `run`, y el arreglo de observables que le pasas tiene forma $(k, 1)$.',
                    level=3,
                    id="e3",
                    hidden=True,
                    hints=[
                        "Necesitas un observable por etiqueta y una sola ejecución del Estimator para todos.",
                        "El Estimator devuelve los valores en un arreglo con la misma forma que el de observables; las barras necesitan una lista plana.",
                        "`graficar` puede reutilizar `valores_esperados` y dibujar con el método de barras de `ejes`.",
                    ],
                ),
            ],
            [A("show", "e1", at="n1"), A("show", "e2", at="n2"), A("show", "e3", at="n3")],
        ),
        beat(
            "proyecto",
            ("", "Proyecto Ising: hito II"),
            """Volvamos al proyecto de la cadena de espines. En el hito uno simulaste dos espines y un paso de tiempo. [[ham]]Hoy tienes todo para generalizarlo: el hamiltoniano de n espines como SparsePauliOp, [[circ]]un circuito de Trotter de varios pasos, [[mag]]y la magnetización como observable, que sigues a lo largo del tiempo.
             [[hito]]El hito dos recalcula lo del hito uno, así que no necesitas nada del cuaderno anterior. Al final comparas tu curva con la evolución exacta.""",
            [
                M(r"H = J\sum_i Z_iZ_{i+1} + h\sum_i X_i", size=44),
                Flow(
                    [
                        dict(t="Hamiltoniano", s="SparsePauliOp"),
                        dict(t="N pasos", s="circuito de Trotter"),
                        dict(t="Magnetización", s="observable"),
                    ],
                    id="f",
                    hidden=True,
                ),
                Mission(
                    "practica/proyecto/hito2.py",
                    [
                        (
                            1,
                            "Escribe el Hamiltoniano de $N$ espines como `SparsePauliOp` y comprueba que con $N=2$ recuperas el hito I.",
                        ),
                        (2, "Construye el circuito de Trotter de varios pasos con `compose`."),
                        (
                            3,
                            "Calcula la curva de magnetización y compárala con la evolución exacta.",
                        ),
                    ],
                    title="Proyecto Ising · Hito II",
                    id="m",
                    hidden=True,
                ),
            ],
            [A("show", "f", at="ham"), A("show", "m", at="hito")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Antes de cerrar la parte, dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda en el navegador.""",
            [T("Una gráfica es un argumento: elige la que responde tu pregunta.", "subtitle")],
            ask=reflect(
                "Quieres explicar a alguien que un estado de Bell está entrelazado. ¿Qué gráfica de esta lección usarías y cuál evitarías? Justifícalo.",
                "Vas a mostrar cómo evoluciona la magnetización de la cadena de Ising con el tiempo. ¿Qué gráfica usarías, y qué pondrías en cada eje?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]draw dibuja circuitos en texto, matplotlib o LaTeX, con muchas opciones. [[r2]]Hay cinco gráficas de estados, más LaTeX. [[r3]]plot histogram para Sampler, barras de matplotlib para Estimator.
             [[r4]]Y timeline draw para ver tiempos. Con esto termina la Parte dos; en la siguiente, la transpilación.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "visualize-circuits",
        "plot-quantum-states",
        "visualize-results",
        "visualize-circuit-timing",
    ],
    practice=[
        "Grafica el estado de la lección con las cinco funciones y guarda cada figura con `savefig`.",
        "Usa `plot_histogram` con `number_to_keep=3` sobre un circuito aleatorio de 4 qubits.",
    ],
)

s_cierre, a_cierre = resumen(
    [
        "el qubit 0 es el bit menos significativo: va a la derecha de la cadena",
        "`n_local` y sus parámetros: una capa de rotaciones más que repeticiones",
        "un observable promedio lleva el coeficiente $1/n$ en cada término",
        "QPY guarda un circuito en memoria sin perder nada",
    ]
)
cierre = lesson(
    "p2-cierre",
    "Cierre de la Parte II: repaso y magnetización",
    "Un repaso corto de la Parte dos y una última función del proyecto Ising: la curva de magnetización de una cadena.",
    [
        "recordar el orden de bits, los parámetros de un circuito N-local, los observables promedio y QPY",
        "calcular la curva de magnetización de una cadena con circuitos de Trotter",
    ],
    [
        beat(
            "repaso1",
            ("", "Repaso: orden de bits"),
            """Empezamos con cuatro preguntas rápidas de lo que viste en esta parte. La primera, sobre el orden de los bits.""",
            [
                Code(
                    """from qiskit import QuantumCircuit

qc = QuantumCircuit(3)
qc.x(2)
qc.measure_all()""",
                    id="c",
                    size=26,
                )
            ],
            ask=choice(
                "Ejecutas el circuito con un Sampler. ¿Qué cadena de bits sale?",
                ["`001`", "`100`", "`010`"],
                1,
                "Correcto: la X actúa sobre el qubit 2, el bit más significativo, y las cadenas se escriben con el qubit 0 a la derecha.",
                wrong=[
                    "Esa sería la X sobre el qubit 0: el qubit 0 es el bit de la derecha.",
                    None,
                    "Eso sería la X sobre el qubit 1.",
                ],
            ),
        ),
        beat(
            "repaso2",
            ("", "Repaso: biblioteca"),
            """Segunda pregunta, sobre la biblioteca de circuitos.""",
            [
                Code(
                    """from qiskit.circuit.library import n_local

circuito = n_local(4, "ry", "cz", reps=2)""",
                    id="c",
                    size=26,
                )
            ],
            ask=numeric(
                "¿Cuántos parámetros tiene `circuito.num_parameters`?",
                12,
                "Correcto: con `reps=2` hay tres capas de rotaciones, una más que las repeticiones, y cada una lleva un ángulo por cada uno de los 4 qubits: $3\\cdot4=12$.",
                tol=0,
                hint="Cuenta las capas de rotaciones: hay una más que las repeticiones.",
            ),
        ),
        beat(
            "repaso3",
            ("", "Repaso: observables"),
            """Tercera pregunta, sobre observables.""",
            [
                Code(
                    """from qiskit.quantum_info import SparsePauliOp

terminos = [("Z", [i], 0.25) for i in range(4)]
Mz = SparsePauliOp.from_sparse_list(terminos, num_qubits=4)""",
                    id="c",
                    size=24,
                )
            ],
            ask=numeric(
                "`Mz` es la magnetización de 4 espines, el promedio de sus $Z$. Si cada término lleva el mismo coeficiente, ¿cuánto vale?",
                0.25,
                "Correcto: un promedio de 4 términos lleva $1/4=0.25$ en cada uno. Con ese coeficiente, todos los espines en $|0\\rangle$ dan $\\langle M_Z\\rangle=1$.",
                tol=0.001,
                hint="Los cuatro coeficientes suman 1 cuando todos los espines valen +1.",
            ),
        ),
        beat(
            "repaso4",
            ("", "Repaso: guardar circuitos"),
            """Última pregunta, sobre cómo guardar un circuito.""",
            [
                Code(
                    """import io
from qiskit import qpy

archivo = io.BytesIO()
qpy.dump(circuito, archivo)""",
                    id="c",
                    size=26,
                )
            ],
            ask=choice(
                "Necesitas guardar un circuito en memoria, sin escribir un archivo, y recuperarlo igual. ¿Qué haces?",
                [
                    "`qpy.dump` sobre un `io.BytesIO` y después `qpy.load`",
                    "`circuito.draw()` y guardar el texto",
                    "`print(circuito.data)` y volver a escribirlo",
                ],
                0,
                "Correcto: QPY escribe en cualquier objeto con forma de archivo, y `qpy.load` devuelve una lista de circuitos.",
                wrong=[
                    None,
                    "Un dibujo no se puede volver a cargar como circuito.",
                    "Eso es una lista de instrucciones, no un formato que se pueda cargar.",
                ],
            ),
        ),
        beat(
            "magnetizacion",
            ("", "Tu turno"),
            """Ahora una última función del proyecto Ising. [[ej]]Ya tienes el circuito de Trotter y la magnetización de la lección anterior. Te falta la curva: la magnetización en cada instante, desde cero hasta el último paso.
             [[n]]Se compara con la evolución exacta de la cadena: si tu curva la sigue, el circuito hace lo que debe.""",
            [
                Exercise(
                    "p2-cierre/curva-trotter",
                    r"Escribe `curva_trotter(n, J, h, dt, K)`: `n` espines, acoplamiento `J`, campo `h`, paso de tiempo `dt` y `K` pasos. Devuelve una lista de `K + 1` números: el valor esperado de `magnetizacion(n)` en los tiempos $k\,dt$, para $k = 0, \dots, K$, con la cadena empezando en $|0\dots0\rangle$. `trotter(n, J, h, dt, pasos)` y `magnetizacion(n)` ya están escritas. Ojo: el punto $k = 0$ también cuenta, y `expectation_value` devuelve un número complejo.",
                    level=3,
                    id="e1",
                    hidden=True,
                    hints=[
                        "Hay un valor por cada número de pasos, empezando en cero.",
                        "Dentro de un bucle sobre `k`, construye el circuito de `k` pasos y conviértelo en un estado.",
                        "Del estado sale el valor esperado con el método de `Statevector`; quédate con su parte real y añádela a `valores`.",
                    ],
                )
            ],
            [A("show", "e1", at="ej")],
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen de la parte. [[r1]]El qubit cero es el bit de la derecha. [[r2]]Los circuitos N-local tienen una capa de rotaciones más que repeticiones. [[r3]]Un observable promedio lleva uno entre n en cada término.
             [[r4]]Y QPY guarda un circuito en memoria. Con esto cierras la Parte dos; en la siguiente, la transpilación.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[],
    practice=[
        "Dibuja la curva de `curva_trotter` junto a la exacta para n = 6 y dt = 0.3. ¿A partir de qué paso se separan?"
    ],
)

LESSONS = [
    circuitos,
    medir,
    orden,
    biblioteca,
    operadores,
    observables,
    control,
    qasm,
    visualizar,
    cierre,
]
