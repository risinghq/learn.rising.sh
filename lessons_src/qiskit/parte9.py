"""Parte IX · Extender e integrar Qiskit."""

from lib import (
    A,
    Box,
    Circ,
    Code,
    Flow,
    G,
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
from parte2 import resumen

# ------------------------------------------------------------------ 9.1 Proveedores
MIQPU = """from qiskit.circuit import Parameter, Measure
from qiskit.circuit.library import CZGate, RZGate, SXGate, XGate
from qiskit.providers import BackendV2, Options
from qiskit.transpiler import Target, InstructionProperties

class MiQPU(BackendV2):
    def __init__(self):
        super().__init__(name="mi_qpu")
        self._target = Target(num_qubits=3)
        theta = Parameter("θ")
        for gate in (RZGate(theta), SXGate(), XGate(), Measure()):
            self._target.add_instruction(gate, {(q,): InstructionProperties(error=1e-4) for q in range(3)})
        self._target.add_instruction(CZGate(), {(0, 1): InstructionProperties(error=1e-2),
                                                (1, 2): InstructionProperties(error=1e-2)})
    @property
    def target(self):
        return self._target
    @property
    def max_circuits(self):
        return None
    @classmethod
    def _default_options(cls):
        return Options(shots=1024)
    def run(self, run_input, **options):
        raise NotImplementedError("aquí se enviaría el trabajo al servicio")

backend = MiQPU()
print(backend.num_qubits, backend.operation_names, backend.coupling_map.get_edges())"""
TRANSPILAR = """from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager

qc = QuantumCircuit(3)
qc.h(0)
qc.cx(0, 2)
isa = generate_preset_pass_manager(1, backend=backend, seed_transpiler=1).run(qc)
print(dict(isa.count_ops()))"""
s_cierre, a_cierre = resumen(
    [
        "un proveedor ofrece un servicio que devuelve un `Target` y un `BackendV2`",
        "la ejecución se expone implementando `BaseSamplerV2` y `BaseEstimatorV2`",
        "resultados con `DataBin`, `PubResult`, `PrimitiveResult`, `BasePrimitiveJob`",
        "de `BackendV1` a `BackendV2`: `configuration()`/`properties()` → `target` y atributos planos",
    ]
)
proveedores = lesson(
    "p9-proveedores",
    "Integrar recursos cuánticos externos",
    "Cómo un proveedor externo integra su hardware en Qiskit: un BackendV2 con su Target, implementaciones de las primitivas, y la migración de BackendV1 a BackendV2.",
    [
        "entender qué necesita un proveedor para integrarse con Qiskit",
        "construir un `BackendV2` mínimo con su `Target`",
        "traducir código de `BackendV1` a `BackendV2`",
    ],
    [
        beat(
            "idea",
            ("", "Proveedores de Qiskit"),
            """Qiskit no es solo para el hardware de IBM. Cualquier organización que ofrezca recursos cuánticos puede integrarlos en Qiskit, y llegar así a todos sus usuarios.
             [[dos]]Para eso necesita dos cosas: [[backends]]un servicio que dé acceso a los backends, con un objeto Target que describa conectividad, puertas base y número de qubits, para que los usuarios puedan transpilar; [[prim]]y una interfaz de ejecución, que implemente las primitivas de Qiskit.""",
            [
                Flow(
                    [
                        dict(t="servicio del proveedor", s="autenticación"),
                        dict(t="`BackendV2` + `Target`", s="para transpilar", color="violet"),
                        dict(
                            t="`BaseSamplerV2` / `BaseEstimatorV2`", s="para ejecutar", color="teal"
                        ),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="dos", i=0),
                A("item", "f", at="backends", i=1),
                A("item", "f", at="prim", i=2),
            ],
        ),
        beat(
            "backend",
            ("", "Un BackendV2 mínimo"),
            """El núcleo de un BackendV2 es su Target. Construyamos uno para un QPU imaginario de tres qubits en línea. [[target]]Añadimos las puertas de un qubit, RZ, raíz de X y X, y la medición, en los tres qubits, con su error; y la CZ solo entre los pares cero uno y uno dos.
             [[metodos]]La clase debe ofrecer el target, el máximo de circuitos por trabajo, las opciones por defecto y run, que en un proveedor real enviaría el trabajo a su servicio.
             [[usar]]Con eso, el backend ya informa sus qubits, sus operaciones y su mapa de acoplamiento: tres qubits, cinco operaciones y solo dos pares conectados.""",
            [
                Code(MIQPU, id="c", size=17),
                Out(
                    "3 ['rz', 'sx', 'x', 'measure', 'cz'] EdgeList[(0, 1), (1, 2)]",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="target", range="9-14"),
                A("hl", "c", at="metodos", range="15-25"),
                A("hl", "c", at="usar", range="27-28"),
                A("show", "o", at="usar", t=3),
            ],
        ),
        beat(
            "predice",
            ("", "Antes de transpilar"),
            """Antes de transpilar, apuesta. Este circuito aplica una Hadamard al qubit cero y una CNOT entre el qubit cero y el dos. Pero en nuestro QPU esos dos qubits no están conectados: solo hay enlaces entre cero y uno, y entre uno y dos.
             ¿Cuántas puertas CZ crees que tendrá el circuito transpilado? Piensa en lo que el transpilador tiene que hacer para llegar de un extremo al otro de la línea.""",
            [Circ(3, [G("h", 0), G("cx", 0, 2)])],
            ask=predict(
                "¿Cuántas CZ tendrá el circuito transpilado?",
                [
                    "ninguna: la CNOT se traduce a otra puerta",
                    "una",
                    "dos",
                    "cuatro o más: hace falta un SWAP",
                ],
                "Anotado. Veamos qué hace el transpilador.",
            ),
        ),
        beat(
            "transpilar",
            ("", "Transpilar para MiQPU"),
            """Transpilamos con el gestor de pases preestablecido, nivel uno, apuntando a nuestro backend. [[res]]Sale una sola CZ, junto con seis rotaciones RZ y tres raíces de X. No hizo falta ningún SWAP: el transpilador colocó los qubits lógicos cero y dos en los físicos uno y cero, que sí son vecinos.
             [[cx]]La CNOT se tradujo a una CZ rodeada de puertas de un qubit, porque la CZ es la única de dos qubits que el Target declara.""",
            [
                Code(TRANSPILAR, id="c", size=22),
                Out("{'rz': 6, 'sx': 3, 'cz': 1}", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="res", lines=[7]),
                A("show", "o", at="res", t=2),
                A("hl", "c", at="cx", lines=[6]),
            ],
        ),
        beat(
            "primitivas",
            ("", "Implementar las primitivas"),
            """Para ejecutar, el proveedor implementa las clases base de las primitivas. Un Estimator propio hereda de BaseEstimatorV2 y su run recibe PUBs y una precisión.
             [[pasos]]Los pasos: fijar una precisión por defecto si no se da; validar el formato de los PUBs; crear un trabajo que herede de BasePrimitiveJob; y enviarlo al servicio. [[datos]]Los resultados se devuelven con las estructuras de Qiskit: DataBin, PubResult y PrimitiveResult.
             [[ref]]Como referencia, Qiskit incluye BackendSamplerV2 y BackendEstimatorV2, que convierten cualquier backend con run en primitivas.""",
            [
                Code(
                    """from qiskit.primitives import BaseEstimatorV2, BasePrimitiveJob

class EstimatorImplementation(BaseEstimatorV2):
    def __init__(self, *, backend, options):
        self._backend = backend
        self._options = options
        self._default_precision = 0.01

    def run(self, pubs, *, precision=None):
        # 1. precisión por defecto  2. validar PUBs
        # 3. crear un BasePrimitiveJob  4. enviarlo al servicio
        ...""",
                    id="c",
                    size=22,
                ),
                T(
                    "resultados: `DataBin` · `PubResult` · `PrimitiveResult` · referencia: `BackendSamplerV2`, `BackendEstimatorV2`",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="primitivas", range="3-7"),
                A("hl", "c", at="pasos", range="9-12"),
                A("show", "n", at="datos"),
            ],
        ),
        beat(
            "v1v2",
            ("", "De BackendV1 a BackendV2"),
            """BackendV1 está obsoleto. Si usas solo qiskit ibm runtime y Aer, no tienes que hacer nada: ya usan BackendV2. Si usas otro proveedor que se actualizó, cambian algunos accesos.
             [[tabla]]La idea: BackendV1 guardaba la información en configuration y properties; BackendV2 la concentra en el Target, con atributos planos. [[cmap]]Un detalle: coupling map ahora devuelve un objeto CouplingMap, no una lista de aristas, y es solo una vista parcial del Target.""",
            [
                Table(
                    ["BackendV1", "BackendV2"],
                    [
                        ["`configuration().n_qubits`", "`num_qubits`"],
                        ["`configuration().basis_gates`", "`operation_names`"],
                        ["`configuration().coupling_map`", "`coupling_map` (objeto `CouplingMap`)"],
                        ["`configuration().max_experiments`", "`max_circuits`"],
                        ["`properties().t1(0)`", "`qubit_properties(0).t1`"],
                        ["`properties().readout_error(0)`", '`target["measure"][(0,)].error`'],
                    ],
                    id="t",
                    stagger=True,
                    size=21,
                )
            ],
            [
                A("item", "t", at="tabla", i=0),
                A("item", "t", at="tabla", t=2, i=1),
                A("item", "t", at="cmap", i=2),
                A("item", "t", at="cmap", t=4, i=3),
                A("item", "t", at="cmap", t=5, i=4),
                A("item", "t", at="cmap", t=6, i=5),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Migra una línea.""",
            [Code("rate = backend.properties().readout_error(3)", norun=True)],
            ask=choice(
                "¿Cuál es el equivalente en BackendV2?",
                [
                    "`backend.readout_error(3)`",
                    '`backend.target["measure"][(3,)].error`',
                    "`backend.qubit_properties(3).readout`",
                ],
                1,
                "Correcto: el error de lectura es el error de la instrucción `measure` en ese qubit, dentro del Target.",
                wrong=[
                    "Ese atributo no existe.",
                    None,
                    "`QubitProperties` solo tiene `t1`, `t2` y `frequency`.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. Abre el cuaderno de práctica con el comando de abajo. [[n1]]Primero reproduces MiQPU y transpilas un circuito. [[n2]]Después le añades duraciones al Target y estimas cuánto dura un circuito. [[n3]]Y por último implementas run con un simulador local, para que MiQPU funcione con las primitivas.
             [[check]]Cada misión tiene una comprobación que se actualiza sola mientras escribes. Todo corre en tu equipo: no hace falta cuenta.""",
            [
                Mission(
                    "practica/p9-proveedores.py",
                    [
                        (
                            1,
                            "Construye `MiQPU` y mira en qué se transpila una CNOT entre qubits lejanos.",
                        ),
                        (2, "Añade duraciones al Target y estima la duración de un circuito."),
                        (
                            3,
                            "Implementa `run` con `BasicSimulator` y úsalo con `BackendSamplerV2`.",
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
            """Antes de cerrar, dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda en tu navegador.""",
            [T("Explicar con tus palabras es la mejor prueba de que entendiste.", "subtitle")],
            ask=reflect(
                "Si el Target de `MiQPU` declarara CX en lugar de CZ, ¿qué cambiaría en el circuito transpilado y qué no? ¿Qué parte del proveedor sigue igual?",
                "Un `BackendV2` solo describe el hardware y la ejecución va en `run`. ¿Por qué crees que Qiskit separa esas dos cosas?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Un proveedor ofrece un BackendV2 con su Target. [[r2]]La ejecución se expone implementando las primitivas. [[r3]]Los resultados usan las estructuras de Qiskit.
             [[r4]]Y al migrar de BackendV1, casi todo pasa al Target.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["create-a-provider", "qiskit-backendv1-to-v2"],
    practice=[
        "Añade a `MiQPU` duraciones en las instrucciones y estima la duración de un circuito con `estimate_duration`.",
        "Envuelve `MiQPU` con `BackendSamplerV2`, implementando `run` con un simulador de Aer.",
    ],
)

# ------------------------------------------------------------------ 9.2 API de C
s_cierre, a_cierre = resumen(
    [
        "API de C experimental: observables, circuitos, `QkDag`, `QkTarget`, pases propios",
        "biblioteca independiente: compilar con Rust, `cbindgen` y un compilador C11 (`make c`)",
        "extensiones de Python: `qiskit.capi.get_include()` + `#define QISKIT_PYTHON_EXTENSION`",
        "compatibilidad solo dentro de la misma versión menor",
    ]
)
OBSERVABLE_C = """#include <stdio.h>
#include <stdint.h>
#include <qiskit.h>

int main(int argc, char *argv[]) {
    uint32_t num_qubits = 100;
    QkObs *obs = qk_obs_zero(num_qubits);
    QkComplex64 coeff = {2, 0};
    QkBitTerm bit_terms[3] = {QkBitTerm_X, QkBitTerm_Y, QkBitTerm_Z};
    uint32_t indices[3] = {0, 1, 2};
    QkObsTerm term = {coeff, 3, bit_terms, indices, num_qubits};
    qk_obs_add_term(obs, &term);
    printf("num_qubits: %i\\n", qk_obs_num_qubits(obs));
    printf("num_terms: %lu\\n", qk_obs_num_terms(obs));
    qk_obs_free(obs);
    return 0;
}"""
c_api = lesson(
    "p9-c-api",
    "La API de C de Qiskit",
    "Usar Qiskit desde C: compilar la biblioteca independiente, construir observables, y escribir extensiones de Python en C para acelerar pases del transpilador.",
    [
        "saber para qué sirve la API de C",
        "compilar un programa en C que use Qiskit",
        "estructurar una extensión de Python escrita en C",
    ],
    [
        beat(
            "por_que",
            ("", "¿Por qué C?"),
            """El núcleo de Qiskit está escrito en Rust, y desde hace poco expone una API de C. Sirve para dos cosas: usar Qiskit desde programas en C, por ejemplo en entornos de supercomputación; [[ext]]y escribir en C las partes críticas de tus extensiones de Python, como un pase de transpilador, para acelerarlas.
             [[exp]]Es experimental: no hay todavía una interfaz binaria estable. Una extensión compilada con la versión dos punto cuatro punto cero funciona con la dos punto cuatro punto uno, pero puede fallar con la dos punto cinco.""",
            [
                Row(
                    Box("def", "Biblioteca independiente", T("programas en C · HPC", "body")),
                    Box(
                        "idea",
                        "Extensiones de Python",
                        T("partes críticas en C", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=24,
                ),
                T(
                    "experimental: compatibilidad solo dentro de la misma versión menor",
                    "note",
                    id="n",
                    hidden=True,
                    color="red",
                ),
            ],
            [A("show", "b", at="ext"), A("show", "n", at="exp")],
        ),
        beat(
            "observable",
            ("", "Un observable en C"),
            """Este programa en C construye un observable de cien qubits. Empieza con un observable cero, [[termino]]y le añade el término dos por X cero, Y uno, Z dos: un coeficiente complejo, los tres operadores de Pauli y los índices de los qubits.
             [[imprimir]]Imprime sus propiedades [[liberar]]y, como en todo programa en C, libera la memoria al final.""",
            [Code(OBSERVABLE_C, "text", id="c", size=19)],
            [
                A("hl", "c", at="observable", range="6-7"),
                A("hl", "c", at="termino", range="8-12"),
                A("hl", "c", at="imprimir", range="13-14"),
                A("hl", "c", at="liberar", lines=[15]),
            ],
        ),
        beat(
            "predice",
            ("", "Antes de compilar"),
            """Antes de compilarlo, apuesta. Mira el fragmento. [[qubits]]El observable se creó con cien qubits. [[term]]Pero solo le añadimos un término, y ese término toca tres qubits.
             [[cual]]¿Qué número de términos crees que imprimirá el programa?""",
            [
                Code(
                    """QkObs *obs = qk_obs_zero(100);
QkObsTerm term = {coeff, 3, bit_terms, indices, 100};   // 2·X0 Y1 Z2
qk_obs_add_term(obs, &term);
printf("num_terms: %lu\\n", qk_obs_num_terms(obs));""",
                    "text",
                    id="c",
                    size=21,
                )
            ],
            [
                A("hl", "c", at="qubits", lines=[1]),
                A("hl", "c", at="term", range="2-3"),
                A("hl", "c", at="cual", lines=[4]),
            ],
            ask=predict(
                "¿Qué imprime `qk_obs_num_terms(obs)`?",
                [
                    "0, porque empieza vacío",
                    "1",
                    "3, uno por cada operador de Pauli",
                    "100, uno por cada qubit",
                ],
                "Anotado. Compilemos y ejecutemos.",
            ),
        ),
        beat(
            "compilar",
            ("", "Compilar y ejecutar"),
            """Para compilar la biblioteca independiente necesitas un compilador de Rust, un compilador de C compatible con C once, cbindgen para generar la cabecera, y la biblioteca de Python, que solo se usa al enlazar.
             [[make]]En la raíz del código de Qiskit, make c genera la biblioteca compartida y la cabecera qiskit punto h. [[gcc]]Luego compilas tu programa enlazando con ella, [[path]]y añades su carpeta a la ruta de bibliotecas antes de ejecutar. [[res]]Imprime cien qubits y un solo término: un término de Pauli es el producto de operadores sobre varios qubits, y no cuenta uno por operador.
             [[win]]En Windows hay dos caminos: para extensiones de Python basta con el compilador de Visual C++, porque las cabeceras vienen con el paquete qiskit; para la biblioteca independiente, se siguen pasos adicionales.""",
            [
                Sh(
                    """make c
gcc example.c -o example.o -I dist/c/include -L dist/c/lib -lqiskit
export LD_LIBRARY_PATH=dist/c/lib:$LD_LIBRARY_PATH
./example.o""",
                    id="c",
                ),
                Out("num_qubits: 100\nnum_terms: 1", id="o", hidden=True),
            ],
            [
                A("hl", "c", at="make", lines=[1]),
                A("hl", "c", at="gcc", lines=[2]),
                A("hl", "c", at="path", range="3-4"),
                A("show", "o", at="res"),
            ],
        ),
        beat(
            "extension",
            ("", "Una extensión de Python en C"),
            """La guía construye una extensión real: una versión en C del pase AddSpectatorMeasures, que viste en la postselección. La estructura: un pyproject y un setup punto py para compilar, un init punto py con la interfaz de Python, y un archivo C con el código rápido.
             [[include]]Desde Qiskit dos punto cuatro, las cabeceras de C vienen con el paquete de Python, y qiskit punto capi punto get include te da su carpeta, que pasas a setuptools. [[ver]]Aquí ves que en este entorno están instaladas.""",
            [
                Code(
                    """import os
import qiskit.capi

print(sorted(os.listdir(qiskit.capi.get_include())))
# setup.py:
# Extension(name="spectator_measures._core",
#           sources=["src/spectator_measures/_coremodule.c"],
#           include_dirs=[qiskit.capi.get_include()])""",
                    id="c",
                    size=22,
                ),
                Out("['qiskit', 'qiskit.h']", id="o", hidden=True, check=True),
                Code(
                    """extension-module
├── pyproject.toml
├── setup.py
└── src/spectator_measures
    ├── __init__.py
    └── _coremodule.c""",
                    "text",
                    id="t",
                    size=20,
                ),
            ],
            [A("hl", "c", at="include", range="5-8"), A("show", "o", at="ver")],
        ),
        beat(
            "capas",
            ("", "Dos capas: Python y C"),
            """En Python, el pase hereda de TransformationPass y su run delega en la función de C. [[macro]]En C, se define la macro QISKIT PYTHON EXTENSION antes de incluir qiskit punto h, y Python punto h va primero.
             [[logica]]La lógica se escribe con tipos de la API de C, QkDag y QkTarget, sin tocar el intérprete. [[puente]]Y una función puente convierte los argumentos de Python con los conversores qk convert from python. [[uso]]Al final, pip install punto, y el pase se usa como cualquier otro.""",
            [
                Code(
                    """class AddSpectatorMeasures(TransformationPass):
    def run(self, dag):
        _core.add_spectator_measures(dag, self.target, ...)   # en C
        return dag""",
                    id="p",
                    norun=True,
                    size=21,
                ),
                Code(
                    """#define QISKIT_PYTHON_EXTENSION
#include <Python.h>
#include <qiskit.h>
static uint32_t add_spectator_measures(QkDag *dag, QkTarget *target, ...);
static PyObject *py_add_spectator_measures(PyObject *self, PyObject *args, PyObject *kwargs);""",
                    "text",
                    id="c",
                    size=19,
                ),
            ],
            [
                A("hl", "p", at="capas", lines=[3]),
                A("hl", "c", at="macro", range="1-3"),
                A("hl", "c", at="logica", lines=[4]),
                A("hl", "c", at="puente", lines=[5]),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Sobre compatibilidad.""",
            [T("Compilaste tu extensión con Qiskit 2.4.0.", "body")],
            ask=choice(
                "¿Con qué versión de Qiskit está garantizado que funcione al ejecutarse?",
                ["con cualquier 2.x", "con 2.4.1", "con 2.5.0"],
                1,
                "Correcto: la API de C es experimental; solo se garantiza dentro de la misma versión menor (2.4.x). Por eso la guía fija `qiskit~=2.4.0` en las dependencias.",
                wrong=[
                    "No: puede romperse entre versiones menores.",
                    None,
                    "2.5.0 es otra versión menor: puede fallar.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. Abre el cuaderno de práctica con el comando de abajo. No necesita compilador de C: usa el mismo observable desde Python. [[n1]]Primero reproduces el observable de cien qubits con un solo término. [[n2]]Después le añades un segundo término, Z en el qubit noventa y nueve. [[n3]]Y por último escribes la función que da la restricción de versión para una extensión.
             [[check]]Cada misión tiene una comprobación que se actualiza sola mientras escribes.""",
            [
                Mission(
                    "practica/p9-c-api.py",
                    [
                        (1, "Construye el observable de 100 qubits y cuenta sus términos."),
                        (
                            2,
                            "Añade un segundo término `Z` en el qubit 99 y comprueba que ahora son dos.",
                        ),
                        (
                            3,
                            "Escribe `restriccion(version)` con la dependencia que fija la versión menor.",
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
            """Antes de cerrar, dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda en tu navegador.""",
            [T("Explicar con tus palabras es la mejor prueba de que entendiste.", "subtitle")],
            ask=reflect(
                "Un colega quiere reescribir en C todo su código de Qiskit «para que vaya más rápido». ¿Qué le preguntarías antes de aconsejarle que lo haga?",
                "La API de C solo garantiza compatibilidad dentro de la misma versión menor. ¿Qué harías en un proyecto para que una actualización de Qiskit no rompa tu extensión sin que te enteres?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]La API de C permite usar Qiskit desde C y acelerar extensiones. [[r2]]La biblioteca se compila con make c. [[r3]]Las extensiones usan get include y la macro QISKIT PYTHON EXTENSION.
             [[r4]]Y por ser experimental, fija la versión menor.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["install-c-api", "c-extension-for-python"],
    practice=[
        "Compila el ejemplo del observable y añádele un segundo término.",
        "Lee la [referencia de la API de C](https://quantum.cloud.ibm.com/docs/en/api/qiskit-c) y busca las funciones para construir un circuito.",
    ],
)

# ------------------------------------------------------------------ 9.3 HPC
s_cierre, a_cierre = resumen(
    [
        "QRMI: capa ligera e independiente del fabricante para acceder a QPUs desde HPC",
        "SPANK plugin: integra QRMI en Slurm · `#SBATCH --qpu=...`",
        "administradores: `qrmi_config.json` y `slurm.conf` · usuarios: `--gres=qpu:N`",
        "aplicaciones: `QRMIService().resources()` · `SamplerV2(qrmi)` · `RUST_LOG` para registros",
    ]
)
SCRIPT_SLURM = """#SBATCH --time=100
#SBATCH --gres=qpu:3
#SBATCH --qpu=my_local_qpu,ibm_fez,ibm_marrakesh
srun python mi_programa.py"""
hpc = lesson(
    "p9-hpc",
    "HPC: QRMI y Slurm",
    "Integrar computadores cuánticos en centros de supercomputación: la interfaz QRMI, el plugin SPANK para Slurm y cómo lo usan administradores, usuarios y aplicaciones.",
    [
        "entender el papel de QRMI en la supercomputación centrada en lo cuántico",
        "pedir QPUs en un trabajo de Slurm",
        "usar QRMI desde una aplicación",
    ],
    [
        beat(
            "qrmi",
            ("", "QRMI"),
            """En un centro de supercomputación, los trabajos se reparten con gestores como Slurm. La interfaz QRMI permite tratar a los QPUs como un recurso más.
             [[que]]Es una biblioteca independiente del fabricante, una capa intermedia ligera que oculta la complejidad de controlar un recurso cuántico con un conjunto simple de operaciones: adquirir, ejecutar, consultar y liberar.
             [[lenguajes]]Está escrita en Rust, con interfaces de C y de Python, y funciona en varias distribuciones de Linux y en macOS. Incluye task runner, una herramienta de línea de comandos para ejecutar cargas cuánticas.""",
            [
                Flow(
                    [
                        dict(t="aplicación HPC"),
                        dict(t="QRMI", s="Rust · C · Python", color="violet"),
                        dict(t="QPU", s="IBM · Pasqal · acceso directo", color="teal"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="qrmi", t=3, i=0),
                A("item", "f", at="que", i=1),
                A("item", "f", at="que", t=6, i=2),
            ],
        ),
        beat(
            "construir",
            ("", "Construir y depurar"),
            """Para construirla: cargo build release para la biblioteca de Rust y C, y maturin para las ruedas de Python, que luego se instalan en los nodos con pip.
             [[log]]Para depurar, la variable de entorno RUST LOG controla los registros: error, warn, que es el valor por defecto, info, debug y trace, que muestra hasta las transacciones HTTP.""",
            [
                Sh(
                    """cargo build --release
CARGO_TARGET_DIR=./target/release/maturin maturin build --release
pip install <rueda>
RUST_LOG=trace <tu programa con QRMI>""",
                    id="c",
                )
            ],
            [A("hl", "c", at="construir", range="1-3"), A("hl", "c", at="log", lines=[4])],
        ),
        beat(
            "spank",
            ("", "El plugin SPANK para Slurm"),
            """El plugin SPANK conecta QRMI con Slurm. Añade una opción a los trabajos: qpu, con la lista de recursos cuánticos que usará.
             [[admin]]El administrador define los recursos en qrmi config punto json: nombre, tipo, que puede ser acceso directo, el servicio de IBM o Pasqal, y las variables de entorno con los puntos de acceso y credenciales. Y en slurm punto conf asigna los QPUs a los nodos como recursos genéricos.
             [[open]]Un detalle: con el servicio de IBM se abre una sesión; si tu plan no las admite, como Open, se configura el modo lote.""",
            [
                Code(
                    """// qrmi_config.json (administrador)
{"resources": [{"name": "ibm_fez", "type": "qiskit-runtime-service",
                "environment": {...}}]}
# slurm.conf
GresTypes=qpu,name
NodeName=node[1-5000] Gres=qpu,name:ibm_fez""",
                    "text",
                    id="c",
                    size=21,
                ),
                T(
                    'plan sin sesiones → `QRMI_IBM_QRS_SESSION_MODE="batch"`',
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [A("hl", "c", at="admin", range="1-6"), A("show", "n", at="open")],
        ),
        beat(
            "usuario",
            ("", "Pedir QPUs en un trabajo"),
            """Como usuario, pides QPUs en tu script de Slurm igual que pides CPUs: con gres igual a qpu y la cantidad, y la opción qpu con los nombres. [[varios]]Puedes pedir varios, incluso de distintos tipos: uno local y dos de IBM.
             [[app]]La idea es que tu código no dependa de un backend concreto: la elección del QPU queda en la definición del recurso, y el trabajo recibe lo que el plugin le deja en el entorno.""",
            [
                Sh(SCRIPT_SLURM, id="c"),
                T(
                    "el plugin deja el resultado en variables de entorno",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="usuario", range="2-3"),
                A("hl", "c", at="varios", lines=[3]),
                A("show", "n", at="app"),
            ],
        ),
        beat(
            "predice",
            ("", "Antes de lanzar el trabajo"),
            """Antes de lanzarlo, apuesta. [[pide]]El script pide tres QPUs. [[admin]]Pero el administrador solo definió dos en qrmi config punto json: my local qpu, de acceso directo, e ibm fez, del servicio de IBM. No hay ninguna entrada para ibm marrakesh.
             [[cual]]Dentro del trabajo, ¿qué valdrá la variable SLURM JOB QPU RESOURCES?""",
            [Sh(SCRIPT_SLURM, id="c")],
            [A("hl", "c", at="pide", lines=[3])],
            ask=predict(
                "Con solo `my_local_qpu` e `ibm_fez` definidos, ¿qué lista `SLURM_JOB_QPU_RESOURCES`?",
                [
                    "`my_local_qpu,ibm_fez,ibm_marrakesh`",
                    "`my_local_qpu,ibm_fez`",
                    "`ibm_fez`",
                    "el trabajo falla porque falta `ibm_marrakesh`",
                ],
                "Anotado. Veámoslo dentro del trabajo.",
            ),
        ),
        beat(
            "entorno",
            ("", "Lo que ve el trabajo"),
            """Dentro del trabajo, el plugin deja dos variables. [[recursos]]SLURM JOB QPU RESOURCES lista los recursos que sí están definidos, en el orden pedido: ibm marrakesh desapareció, sin error. [[tipos]]Y SLURM JOB QPU TYPES da el tipo de cada uno, en el mismo orden.
             [[ig]]Es la misma regla de la pregunta anterior: lo que no está en la configuración se ignora. Por eso conviene que tu programa lea la variable en lugar de fijar el nombre del QPU.""",
            [
                Sh(
                    """echo $SLURM_JOB_QPU_RESOURCES
echo $SLURM_JOB_QPU_TYPES""",
                    id="c",
                ),
                Out(
                    "my_local_qpu,ibm_fez\ndirect-access,qiskit-runtime-service",
                    id="o",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="recursos", lines=[1]),
                A("show", "o", at="recursos"),
                A("hl", "c", at="tipos", lines=[2]),
            ],
        ),
        beat(
            "aplicacion",
            ("", "La aplicación"),
            """En la aplicación, QRMIService te da los recursos asignados. Tomas uno, obtienes su backend para transpilar, [[sampler]]y ejecutas con la primitiva SamplerV2 de QRMI, igual que con las de IBM. [[logs]]Si algo falla, task logs da los registros de la tarea.""",
            [
                Code(
                    """from qrmi.primitives import QRMIService
from qrmi.primitives.ibm import SamplerV2, get_backend

service = QRMIService()
qrmi = service.resources()[0]
backend = get_backend(qrmi)
isa_circuit = generate_preset_pass_manager(1, backend=backend).run(circuit)
job = SamplerV2(qrmi, options={}).run([isa_circuit])
print(job.result()[0].data.meas.get_counts())
# si falla: qrmi.task_logs(job.job_id())""",
                    id="c",
                    norun=True,
                    size=21,
                )
            ],
            [
                A("hl", "c", at="aplicacion", range="4-7"),
                A("hl", "c", at="sampler", range="8-9"),
                A("hl", "c", at="logs", lines=[10]),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Sobre Slurm.""",
            [
                Sh("""#SBATCH --gres=qpu:1
#SBATCH --qpu=ibm_kyiv""")
            ],
            ask=choice(
                "`ibm_kyiv` no está en `qrmi_config.json`. ¿Qué pasa?",
                [
                    "Slurm lo descarga automáticamente",
                    "la especificación se ignora",
                    "se usa el QPU menos ocupado",
                ],
                1,
                "Correcto: si el recurso no está definido en `qrmi_config.json`, la especificación se ignora.",
                wrong=[
                    "Solo se usan los recursos definidos por el administrador.",
                    None,
                    "No hay elección automática en ese caso.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. Abre el cuaderno de práctica con el comando de abajo. No necesita Slurm ni cuenta: repites en Python lo que hace el plugin. [[n1]]Primero reproduces el cruce entre lo que pide el script y lo que define el administrador. [[n2]]Después añades un recurso nuevo a la configuración, con el modo lote. [[n3]]Y por último escribes la función que calcula las variables de entorno del trabajo.
             [[check]]Cada misión tiene una comprobación que se actualiza sola mientras escribes.""",
            [
                Mission(
                    "practica/p9-hpc.py",
                    [
                        (1, "Cruza los QPUs pedidos con los definidos y mira cuál se ignora."),
                        (
                            2,
                            "Añade `ibm_marrakesh` a la configuración con el modo de sesión `batch`.",
                        ),
                        (3, "Escribe `entorno(qpu, config)` con las variables que deja el plugin."),
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
            """Antes de cerrar, dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda en tu navegador.""",
            [T("Explicar con tus palabras es la mejor prueba de que entendiste.", "subtitle")],
            ask=reflect(
                "Un nombre de QPU mal escrito en `--qpu` se ignora sin error. ¿Qué ventaja tiene eso para el centro y qué riesgo corre quien envía el trabajo?",
                "¿Por qué crees que la aplicación debería leer `SLURM_JOB_QPU_RESOURCES` en lugar de fijar el nombre del backend en el código?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]QRMI da acceso a QPUs desde HPC, sin depender del fabricante. [[r2]]El plugin SPANK lo integra en Slurm. [[r3]]El administrador define recursos; el usuario los pide con qpu.
             [[r4]]Y la aplicación los usa con QRMIService y las primitivas de QRMI.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["qrmi", "slurm-plugin", "slurm-hpc-ux"],
    practice=[
        "Lee los [ejemplos de QRMI](https://github.com/qiskit-community/qrmi/tree/main/examples/qiskit_primitives/) para IBM y Pasqal.",
        "Escribe un script de Slurm que pida dos QPUs y 8 CPUs para un flujo SQD.",
    ],
)

# ------------------------------------------------------------------ 9.4 IA
s_cierre, a_cierre = resumen(
    [
        "Qiskit Code Assistant: modelos abiertos entrenados con Qiskit (Mistral, Qwen, Granite) · Ollama, llama.cpp",
        "se integran en VS Code (Continue), JupyterLab (Jupyter AI) o la terminal (OpenCode)",
        "MCP servers: Qiskit, Runtime, Docs, Transpiler, Code Assistant, Gym",
        "skills: instrucciones reutilizables, p. ej. `migrate-qiskit-ibm-runtime`",
    ]
)
ia = lesson(
    "p9-ia",
    "IA para programar con Qiskit",
    "Modelos de lenguaje especializados en Qiskit, servidores MCP para asistentes de IA y skills reutilizables.",
    [
        "ejecutar localmente un modelo de Qiskit Code Assistant",
        "conectar los servidores MCP de Qiskit a un asistente",
        "saber qué es una skill y para qué sirve",
    ],
    [
        beat(
            "assistant",
            ("", "Qiskit Code Assistant"),
            """Qiskit Code Assistant es una familia de modelos de lenguaje entrenados con el código, los ejemplos y la documentación de Qiskit. El modelo actual es mistral small tres punto dos, veinticuatro b, qiskit.
             [[abiertos]]Todos son modelos abiertos, publicados en Hugging Face. Hay versiones GGUF, más ligeras, pensadas para laptops.""",
            [
                Table(
                    ["Modelo", "Parámetros", "Qiskit"],
                    [
                        ["mistral-small-3.2-24b-qiskit", "24 B", "2.2"],
                        ["Qwen2.5-Coder-14B-Qiskit", "14 B", "2.0"],
                        ["granite-3.3-8b-qiskit", "8 B", "2.0"],
                    ],
                    id="t",
                    stagger=True,
                    size=21,
                )
            ],
            [
                A("item", "t", at="assistant", t=5, i=0),
                A("item", "t", at="abiertos", i=1),
                A("item", "t", at="abiertos", t=2, i=2),
            ],
        ),
        beat(
            "predice",
            ("", "Antes de mirar la tabla"),
            """Para medirlos, IBM creó el benchmark Qiskit HumanEval: unas ciento cincuenta tareas de programación con Qiskit, cada una con pruebas unitarias. Tiene una versión difícil, Q H E Hard, que quita la información sobre las importaciones: el modelo debe averiguar solo qué clases y métodos importar. Antes de ver los resultados, apuesta: ¿qué modelo de los tres crees que obtiene la mejor puntuación en la versión difícil?""",
            [
                Table(
                    ["Modelo", "Parámetros", "Qiskit"],
                    [
                        ["mistral-small-3.2-24b-qiskit", "24 B", "2.2"],
                        ["Qwen2.5-Coder-14B-Qiskit", "14 B", "2.0"],
                        ["granite-3.3-8b-qiskit", "8 B", "2.0"],
                    ],
                    id="t",
                )
            ],
            ask=predict(
                "¿Qué modelo puntúa más alto en QHE Hard?",
                [
                    "`mistral-small-3.2-24b-qiskit`",
                    "`Qwen2.5-Coder-14B-Qiskit`",
                    "`granite-3.3-8b-qiskit`",
                    "los tres puntúan casi igual",
                ],
                "Anotado. Veamos los números.",
            ),
        ),
        beat(
            "resultados",
            ("", "Resultados en QHE"),
            """Estos son los resultados, en porcentaje de tareas resueltas. [[hard]]En la versión difícil gana mistral, con treinta y dos coma cuarenta y cinco: sin las importaciones a la vista, es el que más tareas resuelve. [[qhe]]Pero en la versión normal, Qwen de catorce b lo supera: cuarenta y nueve contra cuarenta y siete.
             [[lec]]Granite, de ocho b, queda atrás en ambas. La lección: el tamaño no decide solo. Elige el modelo según el tipo de tarea, y no olvides que cada modelo se entrenó con una versión distinta de Qiskit.""",
            [
                Table(
                    ["Modelo", "QHE Hard", "QHE", "Qiskit"],
                    [
                        ["mistral-small-3.2-24b-qiskit", "32,45", "47,02", "2.2"],
                        ["Qwen2.5-Coder-14B-Qiskit", "25,17", "49,01", "2.0"],
                        ["granite-3.3-8b-qiskit", "14,57", "27,15", "2.0"],
                    ],
                    id="t",
                    stagger=True,
                    size=21,
                ),
                T("el mejor en QHE Hard no es el mejor en QHE", "note", id="n", hidden=True),
            ],
            [
                A("item", "t", at="hard", i=0),
                A("item", "t", at="qhe", i=1),
                A("item", "t", at="lec", i=2),
                A("show", "n", at="lec", t=4),
            ],
        ),
        beat(
            "local",
            ("", "Ejecutarlo en tu equipo"),
            """La forma más sencilla de usarlo en tu equipo es Ollama: un comando descarga el modelo GGUF desde Hugging Face y abre un chat. [[cmds]]Con ollama list ves tus modelos, con ps los cargados, y con rm los borras.
             [[llama]]También puedes usar llama punto cpp. [[editores]]Y conectarlo a tu editor: a VS Code con la extensión Continue, a JupyterLab con Jupyter AI y su comando mágico ai, o a la terminal con OpenCode.""",
            [
                Sh(
                    """ollama run hf.co/Qiskit/Qwen2.5-Coder-14B-Qiskit
ollama list
ollama ps
ollama rm Qwen2.5-Coder-14B-Qiskit""",
                    id="c",
                ),
                Row(
                    Box("def", "VS Code", T("Continue", "body")),
                    Box("def", "JupyterLab", T("Jupyter AI · `%%ai`", "body")),
                    Box("def", "Terminal", T("OpenCode", "body")),
                    id="r",
                    hidden=True,
                    gap=18,
                ),
            ],
            [
                A("hl", "c", at="local", lines=[1]),
                A("hl", "c", at="cmds", range="2-4"),
                A("show", "r", at="editores"),
            ],
        ),
        beat(
            "mcp",
            ("", "Servidores MCP"),
            """El protocolo de contexto de modelos, MCP, permite que un asistente de IA use herramientas externas. Los servidores MCP de Qiskit le dan acceso a Qiskit y a los servicios de IBM.
             [[lista]]Hay varios: el de Qiskit, para crear, transpilar y serializar circuitos en local; el de Runtime, para consultar backends y enviar trabajos; el de documentación; el del transpilador con IA; el de Code Assistant; y uno de la comunidad, Qiskit Gym, con aprendizaje por refuerzo para síntesis de circuitos.
             [[auth]]Los de Qiskit y de documentación no necesitan credenciales; los de Runtime y el transpilador leen tu clave de la variable QISKIT IBM TOKEN.""",
            [
                Table(
                    ["Servidor MCP", "Para qué", "Credenciales"],
                    [
                        ["`qiskit-mcp-server`", "circuitos, transpilar, QASM 3, QPY", "no"],
                        ["`qiskit-ibm-runtime-mcp-server`", "backends y trabajos", "sí"],
                        ["`qiskit-docs-mcp-server`", "buscar en la documentación", "no"],
                        ["`qiskit-ibm-transpiler-mcp-server`", "transpilación con IA", "sí"],
                        ["`qiskit-gym-mcp-server`", "síntesis con aprendizaje por refuerzo", "—"],
                    ],
                    id="t",
                    stagger=True,
                    size=21,
                )
            ],
            [
                A("item", "t", at="lista", i=0),
                A("item", "t", at="lista", t=4, i=1),
                A("item", "t", at="lista", t=7, i=2),
                A("item", "t", at="lista", t=9, i=3),
                A("item", "t", at="lista", t=12, i=4),
            ],
        ),
        beat(
            "config",
            ("", "Configurarlos"),
            """Se instalan con pip, todos juntos o por separado. [[cliente]]Después se declaran en la configuración de tu cliente MCP, como Claude Desktop o Cursor: cada servidor con el comando que lo arranca. [[probar]]Y para probarlos, el inspector de MCP.""",
            [
                Sh(
                    """pip install "qiskit-mcp-servers[all]"
export QISKIT_IBM_TOKEN="<tu_token>"
npx @modelcontextprotocol/inspector qiskit-mcp-server""",
                    id="s",
                ),
                Code(
                    """{"mcpServers": {
  "qiskit": {"command": "qiskit-mcp-server"},
  "qiskit-ibm-runtime": {"command": "qiskit-ibm-runtime-mcp-server"},
  "qiskit-docs": {"command": "qiskit-docs-mcp-server"}
}}""",
                    "text",
                    id="c",
                    hidden=True,
                    size=21,
                ),
            ],
            [
                A("hl", "s", at="config", range="1-2"),
                A("show", "c", at="cliente"),
                A("hl", "s", at="probar", lines=[3]),
            ],
        ),
        beat(
            "skills",
            ("", "Skills"),
            """Por último, las skills de Qiskit: conjuntos de instrucciones reutilizables que enseñan a un asistente de IA a hacer una tarea concreta de forma consistente. Sirven con distintos asistentes.
             [[migrar]]La primera es migrate qiskit ibm runtime, para migrar código: por ejemplo, de las primitivas V1 a las V2, o a las nuevas primitivas del lado del cliente. Se la das al asistente y le dices dónde aplicarla.""",
            [
                Box(
                    "def", "Skill", T("instrucciones reutilizables para una tarea concreta", "body")
                ),
                Code("migrate-qiskit-ibm-runtime", "text", id="c", hidden=True),
            ],
            [A("show", "c", at="migrar")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Elige la herramienta.""",
            [
                T(
                    "Quieres que tu asistente de IA consulte la documentación de Qiskit sin darle credenciales.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué usas?",
                [
                    "el servidor MCP de Runtime",
                    "el servidor MCP de documentación",
                    "un modelo GGUF",
                ],
                1,
                "Correcto: `qiskit-docs-mcp-server` busca en la documentación y no necesita autenticación.",
                wrong=[
                    "Ese necesita tu clave y sirve para backends y trabajos.",
                    None,
                    "Un modelo local no consulta la documentación actual por sí solo.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. Abre el cuaderno de práctica con el comando de abajo. No usa ningún modelo ni red: trae un pequeño banco de pruebas, como el de Qiskit HumanEval, y tres respuestas ya escritas. [[n1]]Primero reproduces la puntuación de tres candidatos. [[n2]]Después corriges el código de uno que escribió una CNOT al revés. [[n3]]Y por último escribes una prueba unitaria que no se deje engañar por respuestas casi correctas.
             [[check]]Cada misión tiene una comprobación que se actualiza sola mientras escribes.""",
            [
                Mission(
                    "practica/p9-ia.py",
                    [
                        (1, "Pasa tres candidatos por las pruebas y lee su puntuación."),
                        (2, "Corrige la CNOT del candidato B para que pase la prueba."),
                        (
                            3,
                            "Escribe `prueba_anti_bell`: debe aceptar el Bell correcto y rechazar dos casi correctos.",
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
            """Antes de cerrar, dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda en tu navegador.""",
            [T("Explicar con tus palabras es la mejor prueba de que entendiste.", "subtitle")],
            ask=reflect(
                "Un modelo te da un circuito que «se ve bien» y que ejecuta sin errores. ¿Qué harías para confiar en él antes de usarlo, y qué no te dice una ejecución sin errores?",
                "¿Qué tareas de tu trabajo con Qiskit delegarías en un asistente y cuáles no? Justifica con un caso concreto.",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Qiskit Code Assistant son modelos abiertos que puedes ejecutar en tu equipo. [[r2]]Se integran en tu editor. [[r3]]Los servidores MCP conectan asistentes con Qiskit y los servicios de IBM.
             [[r4]]Y las skills enseñan tareas concretas, como migrar código.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["qiskit-code-assistant", "qiskit-mcp-servers", "ai-skills"],
    practice=[
        "Instala Ollama y pídele al modelo de Qiskit un circuito GHZ de 5 qubits; verifica el código.",
        "Conecta `qiskit-docs-mcp-server` a tu asistente y pregúntale por las opciones de `EstimatorOptions`.",
    ],
)

# ------------------------------------------------------------------ 9.5 Versiones y migraciones
s_cierre, a_cierre = resumen(
    [
        "versionado semántico X.Y.Z · mayor al menos cada año · menor cada ~3 meses",
        "Qiskit 1.0: fin del metapaquete (`qiskit-terra`) · entorno nuevo · `flake8-qiskit-migration`",
        "Qiskit 2.0: sin `c_if` (usa `if_test`), sin `qiskit.pulse`, `target` en vez de restricciones sueltas",
        "runtime 0.50: Sampler/Estimator del lado del cliente sobre Executor · aprendizaje de ruido explícito",
    ]
)
IF_TEST = """from qiskit.circuit import QuantumCircuit, QuantumRegister, ClassicalRegister

qr, cr = QuantumRegister(2, "q"), ClassicalRegister(2, "c")
qc = QuantumCircuit(qr, cr)
qc.h([0, 1])
qc.measure(qr, cr)
# antes: qc.x(0).c_if(cr, 3)
with qc.if_test((cr, 3)):
    qc.x(0)
print(dict(qc.count_ops()))"""
migraciones = lesson(
    "p9-migraciones",
    "Versiones y migraciones",
    "La estrategia de versiones de Qiskit, las migraciones a 1.0 y 2.0, el paso a las primitivas del lado del cliente y cómo seguir las novedades.",
    [
        "entender el versionado y el ciclo de soporte de Qiskit",
        "migrar código de Qiskit 1.x a 2.x",
        "pasar a las primitivas del lado del cliente",
    ],
    [
        beat(
            "semver",
            ("", "Versionado semántico"),
            """Qiskit sigue el versionado semántico: mayor punto menor punto parche. [[mayor]]Los cambios incompatibles solo llegan en versiones mayores, como mínimo una vez al año. [[menor]]Las menores, aproximadamente cada tres meses, añaden funciones sin romper nada. [[parche]]Y los parches corrigen errores.
             [[soporte]]Cuando sale una mayor, la anterior recibe correcciones de errores al menos seis meses, y de seguridad un año. Por eso las bibliotecas que dependen de Qiskit no deberían exigir la nueva mayor de inmediato.
             [[api]]La API pública es todo lo documentado que no empieza con guion bajo. Las versiones de Python y de las dependencias no forman parte de la garantía.""",
            [
                M(
                    r"\underbrace{2}_{\text{mayor}}\,.\,\underbrace{5}_{\text{menor}}\,.\,\underbrace{2}_{\text{parche}}",
                    size=50,
                ),
                Table(
                    ["Versión", "Frecuencia", "Contenido"],
                    [
                        ["mayor", "≥ 1 año", "cambios incompatibles"],
                        ["menor", "~ 3 meses", "funciones nuevas"],
                        ["parche", "cuando haga falta", "correcciones"],
                    ],
                    id="t",
                    stagger=True,
                    size=23,
                ),
                T(
                    "la mayor anterior: errores ≥ 6 meses · seguridad 1 año",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("item", "t", at="mayor", i=0),
                A("item", "t", at="menor", i=1),
                A("item", "t", at="parche", i=2),
                A("show", "n", at="soporte"),
            ],
        ),
        beat(
            "v1",
            ("", "Qiskit 1.0: el fin del metapaquete"),
            """Antes de la uno punto cero, el paquete qiskit era un metapaquete sin código propio: el núcleo vivía en qiskit terra, junto a Aer, el proveedor de IBM y otros paquetes.
             [[cambio]]Qiskit uno punto cero volvió a la estructura simple de cualquier paquete de Python: qiskit contiene el código. Fue un cambio único: [[entorno]]no se puede actualizar un entorno viejo en su sitio; hay que crear un entorno virtual nuevo, y un archivo de restricciones impide que alguna dependencia reinstale qiskit terra.
             [[herramienta]]Para el código, flake8 qiskit migration detecta importaciones eliminadas, como qiskit punto Aer o execute, y sugiere alternativas.""",
            [
                Row(
                    Box(
                        "warn",
                        "antes de 1.0",
                        T("`qiskit` = metapaquete · código en `qiskit-terra`", "body"),
                    ),
                    Box(
                        "idea",
                        "desde 1.0",
                        T("`qiskit` contiene el código", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=24,
                ),
                Sh(
                    """python -m venv .venv
pip install -c https://qisk.it/1-0-constraints qiskit
pipx run flake8-qiskit-migration src/""",
                    id="c",
                    hidden=True,
                ),
            ],
            [
                A("show", "b", at="cambio"),
                A("show", "c", at="entorno"),
                A("hl", "c", at="entorno", range="1-2"),
                A("hl", "c", at="herramienta", lines=[3]),
            ],
        ),
        beat(
            "predice_if",
            ("", "Qiskit 2.0: antes de ejecutar"),
            """Qiskit dos punto cero rompió compatibilidad sin cambiar la estructura de paquetes. Tres cambios principales; empecemos por el primero. [[cif]]Desaparece c if: las condiciones se escriben con un bloque if test, que ya viste en la Parte dos.
             [[cual]]Este circuito mide dos qubits y aplica una X al qubit cero solo si se midió uno uno. Antes de ejecutarlo, apuesta: ¿qué operaciones contará count ops?""",
            [
                Code(
                    """qc.h([0, 1])
qc.measure(qr, cr)
with qc.if_test((cr, 3)):
    qc.x(0)""",
                    id="c",
                    size=22,
                    norun=True,
                )
            ],
            [A("hl", "c", at="cif", range="3-4")],
            ask=predict(
                "¿Qué devuelve `dict(qc.count_ops())`?",
                [
                    "`{'h': 2, 'measure': 2, 'x': 1}`",
                    "`{'h': 2, 'measure': 2, 'if_else': 1}`",
                    "`{'h': 2, 'measure': 2, 'x': 1, 'if_else': 1}`",
                    "`{'h': 2, 'measure': 2, 'if_test': 1}`",
                ],
                "Anotado. Veamos qué cuenta Qiskit.",
            ),
        ),
        beat(
            "v2",
            ("", "Qiskit 2.0"),
            """[[cif]]La condición no es una puerta con un decorador: es una sola instrucción, if else, que contiene el bloque. Por eso la X no aparece en el recuento de nivel superior.
             [[dur]]Segundo cambio: las instrucciones ya no tienen duration ni unit; las duraciones se consultan en el Target, y para la duración del circuito, estimate duration.
             [[pulse]]Y tercero: qiskit punto pulse se eliminó por completo, con todo lo relacionado con calibraciones.""",
            [
                Code(IF_TEST, id="c", size=22),
                Out("{'h': 2, 'measure': 2, 'if_else': 1}", id="o", hidden=True, check=True),
                Code(
                    """# antes: instruction.duration
duration = getattr(target["cx"][2, 4], "duration", None)""",
                    id="d",
                    hidden=True,
                    size=21,
                    setup="from qiskit.providers.fake_provider import GenericBackendV2\ntarget = GenericBackendV2(5, seed=1).target",
                ),
            ],
            [
                A("hl", "c", at="cif", range="7-9"),
                A("show", "o", at="cif", t=1),
                A("show", "d", at="dur"),
            ],
        ),
        beat(
            "v2_transp",
            ("", "El transpilador en 2.0"),
            """En el transpilador, se acabaron casi todas las restricciones sueltas: backend properties, instruction durations y timing constraints ya no se aceptan. Lo que antes pasabas por separado, ahora va en un Target.
             [[como]]Puedes construirlo desde cero, partir de GenericBackendV2, o usar Target punto from configuration. [[mezcla]]Y pasar coupling map o basis gates junto con un backend da un aviso: habría dos fuentes de verdad.""",
            [
                Code(
                    """from qiskit import QuantumCircuit
from qiskit.circuit.library import CXGate, XGate
from qiskit.transpiler import Target, InstructionProperties, generate_preset_pass_manager

target = Target(num_qubits=2)
target.add_instruction(CXGate(), {(0, 1): InstructionProperties(error=1e-4, duration=5e-7)})
target.add_instruction(XGate(), {(0,): InstructionProperties(error=1e-5, duration=5e-8),
                                 (1,): InstructionProperties(error=2e-5, duration=6e-8)})
pm = generate_preset_pass_manager(target=target)
print(pm.run(QuantumCircuit(2)).num_qubits)""",
                    id="c",
                    size=20,
                ),
                Out("2", id="o", hidden=True, check=True),
            ],
            [A("hl", "c", at="como", range="5-9"), A("show", "o", at="como", t=3)],
        ),
        beat(
            "cliente",
            ("", "Primitivas del lado del cliente"),
            """El cambio más reciente: desde qiskit ibm runtime cero punto cincuenta, Sampler y Estimator se reimplementan del lado del cliente, sobre Executor. Antes eran una caja negra en el servidor; ahora puedes inspeccionar lo que hacen.
             [[imports]]La migración es casi solo cambiar las importaciones; pronto, las de siempre apuntarán a las nuevas. [[igual]]Se mantienen el modo, las opciones, la firma de run, los PUBs y los resultados.""",
            [
                Code(
                    """
from qiskit_ibm_runtime.executor_sampler import Sampler
from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.options_models import SamplerOptions, EstimatorOptions""",
                    id="c",
                    size=21,
                ),
                T(
                    "igual: `mode`, opciones, `run()`, PUBs y resultados",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [A("hl", "c", at="imports", range="4-6"), A("show", "n", at="igual")],
        ),
        beat(
            "predice_opciones",
            ("", "Las opciones, antes de ejecutar"),
            """Las opciones del Estimator también cambiaron. [[pydantic]]Ahora son modelos de Pydantic, con campos validados. Fíjate en esta asignación: seed estimator era una opción de la versión anterior, y ya no existe. [[cual]]Antes de ejecutar, apuesta: ¿qué pasa al asignarla?""",
            [
                Code(
                    """from qiskit_ibm_runtime.options_models import EstimatorOptions

options = EstimatorOptions()
options.default_shots = 2000
options.seed_estimator = 1""",
                    id="c",
                    size=24,
                    norun=True,
                )
            ],
            [A("hl", "c", at="pydantic", lines=[4]), A("hl", "c", at="cual", lines=[5])],
            ask=predict(
                "¿Qué ocurre en `options.seed_estimator = 1`?",
                [
                    "se acepta y fija la semilla",
                    "se acepta y se ignora sin avisar",
                    "`AttributeError`",
                    "`ValidationError`",
                ],
                "Anotado. Lo comprobamos en la siguiente pantalla.",
            ),
        ),
        beat(
            "diferencias",
            ("", "Qué cambia"),
            """Algunas diferencias. [[pydantic]]Las opciones son modelos de Pydantic. En lugar de asdict, usa model dump; y las opciones eliminadas, como seed estimator, dan error de validación.
             [[mezcla]]No se pueden mezclar disparos o precisiones distintos en un trabajo: agrupa los PUBs por valor, un trabajo por grupo, todos en un lote. [[ruido]]Y para PEA y PEC ya no hay aprendizaje de ruido implícito: lo haces tú con NoiseLearnerV3 y pasas el modelo al Estimator.
             [[local]]Para probar en local con un backend falso, la guía sugiere cliffordizar el circuito ISA, con ConvertISAToClifford: se simula rápido, pero pierde el layout, así que el observable se adapta con el layout del circuito original.""",
            [
                Code(
                    """from qiskit import QuantumCircuit
from qiskit.transpiler import PassManager, generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez
from qiskit_ibm_runtime.transpiler.passes import ConvertISAToClifford
from qiskit_ibm_runtime.options_models import EstimatorOptions

options = EstimatorOptions()
options.default_shots = 2000
print(options.model_dump()["default_shots"])
try:
    options.seed_estimator = 1
except Exception as e:
    print(type(e).__name__)

qc = QuantumCircuit(2)
qc.rx(0.3, 0)
qc.cx(0, 1)
isa = generate_preset_pass_manager(1, backend=FakeFez(), seed_transpiler=1).run(qc)
clifford = PassManager([ConvertISAToClifford()]).run(isa)
print(clifford.layout)""",
                    id="c",
                    size=18,
                ),
                Out("2000\nValidationError\nNone", id="o", hidden=True, check=True),
            ],
            [
                A("hl", "c", at="pydantic", range="7-13"),
                A("show", "o", at="pydantic", t=4),
                A("hl", "c", at="local", range="15-20"),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Divide el trabajo.""",
            [
                T(
                    "Tienes PUBs A y C con precisión 0,01, y B con precisión 0,05. Usas el Estimator del lado del cliente.",
                    "body",
                )
            ],
            ask=numeric(
                "¿Cuántos trabajos envías como mínimo?",
                2,
                "Correcto: uno con [A, C] a 0,01 y otro con [B] a 0,05, ambos dentro de un `Batch`, enviando los dos antes de pedir resultados.",
                tol=0.0001,
                hint="Un trabajo por valor distinto de precisión, no por PUB.",
            ),
        ),
        beat(
            "novedades",
            ("", "Seguir las novedades"),
            """Para estar al día, la documentación tiene registros de cambios: del SDK, del cliente y del servicio de computación cuántica, del servicio de transpilación, de los addons, de Functions y de las skills.
             [[recientes]]Algunas novedades recientes: el servicio Qiskit Runtime pasó a llamarse IBM Quantum Compute Service; llegó ibm phoenix, el primer Nighthawk r2, con reset rápido, un rep delay de un microsegundo y más de cien mil circuitos por segundo; y Composer admite OpenQASM tres.""",
            [
                L(
                    [
                        "SDK de Qiskit · cliente y servicio de computación cuántica",
                        "servicio de transpilación · addons · Functions · skills",
                    ],
                    id="l",
                ),
                Table(
                    ["Fecha", "Novedad"],
                    [
                        ["jul 2026", "Qiskit Runtime → IBM Quantum Compute Service"],
                        [
                            "sep 2026",
                            "`ibm_phoenix` (Nighthawk r2): `rep_delay` 1 µs, > 100 000 MCPS",
                        ],
                        ["sep 2026", "runtime 0.50: primitivas del lado del cliente"],
                        ["ago 2026", "Composer con OpenQASM 3"],
                    ],
                    id="t",
                    hidden=True,
                    stagger=True,
                    size=21,
                ),
            ],
            [
                A("show", "t", at="recientes"),
                A("item", "t", at="recientes", i=0),
                A("item", "t", at="recientes", t=4, i=1),
                A("item", "t", at="recientes", t=9, i=2),
                A("item", "t", at="recientes", t=11, i=3),
            ],
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. Abre el cuaderno de práctica con el comando de abajo. Todo corre en tu equipo. [[n1]]Primero migras un circuito de c if a if test. [[n2]]Después conviertes las opciones del Estimator a un diccionario con model dump. [[n3]]Y por último escribes la función que reparte los PUBs en un trabajo por valor de precisión.
             [[check]]Cada misión tiene una comprobación que se actualiza sola mientras escribes.""",
            [
                Mission(
                    "practica/p9-migraciones.py",
                    [
                        (1, "Migra una condición de `c_if` a `if_test` y cuenta sus operaciones."),
                        (2, "Convierte `EstimatorOptions` en un diccionario con `model_dump`."),
                        (3, "Escribe `dividir(pubs)`: un grupo por cada valor de precisión."),
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
            ("", "Tu proyecto: el hito IX"),
            """Esta lección cierra la Parte nueve, y con ella llega el hito nueve del proyecto de la cadena de espines. [[migrar]]Migras el código del proyecto a las primitivas del lado del cliente: el Estimator para la magnetización y el Sampler para los conteos. [[paquete]]Y lo empaquetas como un módulo que puedes importar, ising punto py, para que el informe final lo reutilice.
             [[hito]]El cuaderno recalcula primero lo de los hitos anteriores, para que no dependas de ningún otro cuaderno.""",
            [
                Row(
                    Box(
                        "warn",
                        "Antes",
                        T("`StatevectorEstimator` · funciones sueltas", "body"),
                        id="a",
                        hidden=True,
                    ),
                    Box(
                        "idea",
                        "Ahora",
                        T("`executor_estimator.Estimator` · módulo `ising`", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=24,
                ),
                Mission(
                    "practica/proyecto/hito9.py",
                    [
                        (
                            1,
                            "Recalcula el Hamiltoniano, el circuito de Trotter y la curva exacta de los hitos anteriores.",
                        ),
                        (
                            2,
                            "Cambia la importación al `Estimator` del lado del cliente y compara con la curva ideal.",
                        ),
                        (
                            3,
                            "Escribe `magnetizacion_conteos` y calcula la magnetización con el `Sampler`.",
                        ),
                    ],
                    title="Proyecto Ising · Hito IX",
                    id="m",
                    hidden=True,
                ),
            ],
            [A("show", "a", at="migrar"), A("show", "b", at="paquete"), A("show", "m", at="hito")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Antes de cerrar la parte, dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda en tu navegador.""",
            [T("Explicar con tus palabras es la mejor prueba de que entendiste.", "subtitle")],
            ask=reflect(
                "Qiskit separa cambios incompatibles (versión mayor) de funciones nuevas (versión menor). ¿Cómo usarías eso para decidir cuándo actualizar un proyecto que depende de Qiskit?",
                "En la migración al Estimator del lado del cliente, ¿qué cosas esperas que sigan funcionando igual y cuáles revisarías primero? ¿Cómo lo comprobarías sin una cuenta?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Qiskit usa versionado semántico, con soporte extendido para la mayor anterior. [[r2]]La uno punto cero eliminó el metapaquete. [[r3]]La dos punto cero quitó c if, pulse y las restricciones sueltas.
             [[r4]]Y las primitivas pasan al lado del cliente. Con esto termina la Parte nueve.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "qiskit-sdk-version-strategy",
        "qiskit-2.0",
        "qiskit-1.0",
        "metapackage-migration",
        "qiskit-1.0-installation",
        "qiskit-1.0-features",
        "migrate-to-client-side-primitives",
        "changelog-quantum-compute-service",
        "changelog-qiskit",
        "changelog-quantum-compute",
        "changelog-qiskit-transpiler",
        "changelog-qiskit-addons",
        "changelog-qiskit-functions",
        "changelog-qiskit-skills",
    ],
    practice=[
        "Ejecuta `flake8-qiskit-migration` sobre un cuaderno viejo de Qiskit 0.x y corrige lo que encuentre.",
        "Migra a las primitivas del lado del cliente un script tuyo con Estimator y compara `job.inputs` antes y después.",
    ],
)

LESSONS = [proveedores, c_api, hpc, ia, migraciones]
