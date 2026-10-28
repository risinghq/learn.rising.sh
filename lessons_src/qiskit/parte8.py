"""Parte VIII · Serverless, addons y Qiskit Functions."""

from lib import (
    A,
    Box,
    Code,
    Flow,
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
    predict,
    reflect,
)
from parte2 import resumen

# ------------------------------------------------------------------ 8.1 Qiskit Serverless
s_cierre, a_cierre = resumen(
    [
        "programa remoto: `get_arguments` → trabajo → `save_result`",
        "`QiskitFunction(title, entrypoint, working_dir)` + `serverless.upload` · `load(...).run(...)`",
        '`@distribute_task(target={"cpu": 1})` + `get(refs)` para paralelizar',
        "dentro del programa: `get_runtime_service()` · datos en `/data` (solo `tar`, `h5`)",
    ]
)
serverless = lesson(
    "p8-serverless",
    "Qiskit Serverless",
    "Ejecutar flujos cuánticos-clásicos completos en la nube de IBM: escribir un programa, subirlo, ejecutarlo, paralelizar tareas, gestionar datos y portar código existente.",
    [
        "escribir y subir un programa de Qiskit Serverless",
        "ejecutarlo, seguir su estado y recuperar resultados y registros",
        "paralelizar tareas clásicas con `distribute_task`",
    ],
    [
        beat(
            "que",
            ("", "¿Para qué sirve?"),
            """Qiskit Serverless te deja ejecutar el patrón completo de Qiskit en la nube de IBM, no solo la parte cuántica. Es experimental y solo está disponible en los planes Premium, Flex y On-Prem.
             [[usos]]Sirve para tres cosas: paralelizar tareas clásicas, como el preprocesamiento y el posprocesamiento; mantener vivos trabajos largos aunque apagues tu computadora; y desplegar programas reutilizables.
             [[recursos]]Por defecto, cada nodo normal tiene veinticuatro núcleos y ciento veinte gigas de RAM, con hasta dos trabajos activos por usuario; también hay nodos con GPU.
             [[paquetes]]Se instalan dos paquetes: qiskit ibm catalog, el cliente que sube y ejecuta programas, y qiskit serverless, las herramientas del lado del servidor. Ambos piden Python tres punto once o posterior.""",
            [
                L(
                    [
                        "paralelizar preprocesamiento y posprocesamiento",
                        "trabajos largos que siguen aunque apagues tu equipo",
                        "programas reutilizables",
                    ],
                    id="l",
                    stagger=True,
                ),
                Table(
                    ["Nodo", "Recursos", "Trabajos activos"],
                    [["normal", "24 vCPU · 120 GB", "2"], ["GPU (L40S)", "24 vCPU · 120 GB", "4"]],
                    id="t",
                    hidden=True,
                    size=23,
                ),
                Sh("pip install qiskit-ibm-catalog qiskit_serverless", id="c", hidden=True),
            ],
            [
                A("item", "l", at="usos", i=0),
                A("item", "l", at="usos", t=3, i=1),
                A("item", "l", at="usos", t=6, i=2),
                A("show", "t", at="recursos"),
                A("show", "c", at="paquetes"),
            ],
        ),
        beat(
            "programa",
            ("", "Escribir el programa"),
            """Un programa de Serverless es un archivo de Python dentro de una carpeta propia, por ejemplo source files, que se sube entera.
             [[args]]El programa lee sus entradas con get arguments. Solo admite entradas serializables: por eso se pasa el nombre del backend como texto, no el objeto backend.
             [[servicio]]Dentro del programa, el servicio se crea con get runtime service, no con QiskitRuntimeService. Así los trabajos que lance quedan vinculados al trabajo de Serverless, para su estado, registros y uso.
             [[guardar]]Al final, save result devuelve los resultados.""",
            [
                Code(
                    """# source_files/transpile_remote.py
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_serverless import get_arguments, save_result, get_runtime_service

arguments = get_arguments()
circuits = arguments.get("circuits")
backend_name = arguments.get("backend_name")
optimization_level = arguments.get("optimization_level")

service = get_runtime_service()
backend = service.backend(backend_name)
pm = generate_preset_pass_manager(optimization_level=optimization_level, backend=backend)

save_result({"transpiled_circuits": [pm.run(c) for c in circuits]})""",
                    id="c",
                    norun=True,
                    size=21,
                )
            ],
            [
                A("hl", "c", at="args", range="5-8"),
                A("hl", "c", at="servicio", range="10-11"),
                A("hl", "c", at="guardar", lines=[14]),
            ],
        ),
        beat(
            "subir",
            ("", "Subirlo"),
            """Para subirlo, te autenticas con QiskitServerless, usando tu clave de API guardada. [[funcion]]Luego describes el programa con QiskitFunction: un título, el archivo de entrada, entrypoint, y la carpeta de trabajo, working dir.
             [[upload]]upload comprime la carpeta, la sube y limpia el archivo temporal. [[list]]Y serverless punto list muestra tus programas, para confirmar que está ahí. También puedes declarar dependencias de pip.""",
            [
                Code(
                    """from qiskit_ibm_catalog import QiskitServerless, QiskitFunction

serverless = QiskitServerless()
transpile_remote = QiskitFunction(
    title="transpile_remote_serverless",
    entrypoint="transpile_remote.py",
    working_dir="./source_files/",
)
serverless.upload(transpile_remote)
serverless.list()""",
                    id="c",
                    norun=True,
                    size=22,
                ),
                Out("[QiskitFunction(transpile_remote_serverless)]", id="o", hidden=True),
            ],
            [
                A("hl", "c", at="subir", lines=[3]),
                A("hl", "c", at="funcion", range="4-8"),
                A("hl", "c", at="upload", lines=[9]),
                A("hl", "c", at="list", lines=[10]),
                A("show", "o", at="list", t=1),
            ],
        ),
        beat(
            "ejecutar",
            ("", "Ejecutarlo"),
            """Para ejecutarlo, lo cargas con load y lo llamas con run, pasando las entradas como argumentos con nombre, igual que una función de Python.
             [[estado]]job punto status recorre los estados: en cola, inicializando, mientras se prepara el entorno e instalan dependencias, ejecutándose y terminado.
             [[logs]]Mientras se ejecuta, job punto logs te da lo que el programa imprime; [[result]]al terminar, job punto result devuelve lo guardado con save result. [[stop]]Y job punto stop lo detiene.""",
            [
                Code(
                    """program = serverless.load("transpile_remote_serverless")
job = program.run(circuits=circuits, backend_name="ibm_fez", optimization_level=3)
job.status()        # QUEUED → INITIALIZING → RUNNING → DONE
job.logs()          # salidas de print()
job.result()        # {"transpiled_circuits": [...]}
job.stop()
serverless.jobs()   # trabajos anteriores""",
                    id="c",
                    norun=True,
                    size=22,
                ),
                Flow(
                    [
                        dict(t="QUEUED"),
                        dict(t="INITIALIZING", s="entorno y dependencias"),
                        dict(t="RUNNING", s="`logs()`", color="gold"),
                        dict(t="DONE", s="`result()`", color="teal"),
                    ],
                    id="f",
                    hidden=True,
                    stagger=True,
                ),
            ],
            [
                A("hl", "c", at="ejecutar", range="1-2"),
                A("show", "f", at="estado"),
                A("item", "f", at="estado", i=0),
                A("item", "f", at="estado", t=1, i=1),
                A("item", "f", at="estado", t=4, i=2),
                A("item", "f", at="estado", t=6, i=3),
                A("hl", "c", at="logs", lines=[4]),
                A("hl", "c", at="result", lines=[5]),
                A("hl", "c", at="stop", range="6-7"),
            ],
        ),
        beat(
            "estados",
            ("", "Estados detallados"),
            """Dentro del programa puedes anunciar en qué etapa estás, con update status. Los estados detallados siguen el patrón: mapeando el problema, optimizando para el hardware, esperando al QPU, ejecutando en el QPU y posprocesando.
             [[auto]]Al terminar con save result, el estado pasa a terminado automáticamente.""",
            [
                Code(
                    """from qiskit_serverless import update_status, Job

update_status(Job.MAPPING)              # RUNNING: MAPPING
update_status(Job.OPTIMIZING_HARDWARE)  # RUNNING: OPTIMIZING_FOR_HARDWARE
update_status(Job.WAITING_QPU)          # RUNNING: WAITING_FOR_QPU
update_status(Job.EXECUTING_QPU)        # RUNNING: EXECUTING_QPU
update_status(Job.POST_PROCESSING)      # RUNNING: POST_PROCESSING""",
                    id="c",
                    norun=True,
                    size=21,
                )
            ],
            [
                A("hl", "c", at="estados", range="3-7"),
                A("hl", "c", at="auto", lines=[7], dim=False),
            ],
        ),
        beat(
            "predice",
            ("", "Antes de paralelizar"),
            """Antes de ver cómo se paraleliza, apuesta. [[codigo]]Esta función lleva el decorador distribute task, y la llamamos una vez con un circuito. [[cual]]¿Qué crees que es x justo después de la llamada? No hace falta que sepas la respuesta: equivocarse en una predicción enseña más que acertar por memoria.""",
            [
                Code(
                    """@distribute_task(target={"cpu": 1})
def transpile_remote(circuit, optimization_level, backend):
    pm = generate_preset_pass_manager(optimization_level=optimization_level,
                                      backend=service.backend(backend))
    return pm.run(circuit)

x = transpile_remote(circuit, 3, backend)""",
                    id="c",
                    norun=True,
                    size=21,
                )
            ],
            [A("hl", "c", at="codigo", range="1-5"), A("hl", "c", at="cual", lines=[7])],
            ask=predict(
                "¿Qué es `x` justo después de la llamada?",
                [
                    "el circuito transpilado",
                    "una referencia a una tarea asíncrona",
                    "una lista con el circuito",
                    "`None`, hasta que llames a `get`",
                ],
                "Anotado. Veamos qué hace el decorador.",
            ),
        ),
        beat(
            "paralelo",
            ("", "Paralelizar"),
            """La ventaja principal: paralelizar trabajo clásico. Decoras una función con distribute task, indicando los recursos que necesita cada tarea, por ejemplo un núcleo.
             [[refs]]Esta es la respuesta a tu apuesta: cada llamada ya no devuelve el resultado, sino una referencia a una tarea asíncrona que corre en su propio trabajador. [[get]]get, con la lista de referencias, espera y reúne los resultados.
             [[recursos]]Puedes pedir núcleos completos o fracciones, y memoria en bytes: dos gigas son dos por mil veinticuatro al cubo.""",
            [
                Code(
                    """from qiskit_serverless import distribute_task, get

@distribute_task(target={"cpu": 1})
def transpile_remote(circuit, optimization_level, backend):
    pm = generate_preset_pass_manager(optimization_level=optimization_level,
                                      backend=service.backend(backend))
    return pm.run(circuit)

refs = [transpile_remote(c, 3, backend) for c in circuit_list]   # en paralelo
transpiled = get(refs)

# @distribute_task(target={"cpu": 16, "mem": 2 * 1024**3})""",
                    id="c",
                    norun=True,
                    size=21,
                )
            ],
            [
                A("hl", "c", at="paralelo", lines=[3]),
                A("hl", "c", at="refs", lines=[9]),
                A("hl", "c", at="get", lines=[10]),
                A("hl", "c", at="recursos", lines=[12]),
            ],
        ),
        beat(
            "datos",
            ("", "Gestionar datos"),
            """Serverless tiene un directorio de datos compartido entre tus programas, con dos limitaciones: solo archivos tar y h5, y sin subcarpetas.
             [[subir]]file upload sube un archivo asociado a una función, files los lista, [[bajar]]y desde el programa, file download lo descarga para descomprimirlo y usarlo como en local. file delete lo borra.""",
            [
                Code(
                    """serverless.file_upload(file="transpile_demo.tar", function=transpile_remote)
serverless.files(function=transpile_remote)
# dentro del programa:
path = serverless.file_download(serverless.files()[0])
serverless.file_delete(...)""",
                    id="c",
                    norun=True,
                    size=22,
                ),
                T("solo `tar` y `h5` · directorio plano `/data`", "note", id="n"),
            ],
            [A("hl", "c", at="subir", range="1-2"), A("hl", "c", at="bajar", range="3-5")],
        ),
        beat(
            "portar",
            ("", "Portar código existente"),
            """¿Cómo pasas a Serverless un experimento que ya tienes en local? [[pasos]]Cambia las variables de entrada por get arguments; crea el servicio con get runtime service; decora con distribute task lo que quieras paralelizar y reúne con get; y devuelve con save result en lugar de imprimir.
             [[try]]La guía recomienda además envolver el trabajo en un try, e imprimir la traza de cualquier excepción, para verla después en los registros.""",
            [
                Table(
                    ["En local", "En Serverless"],
                    [
                        ["variables en el cuaderno", "`get_arguments()`"],
                        ["`QiskitRuntimeService()`", "`get_runtime_service()`"],
                        ["bucle secuencial", "`@distribute_task` + `get(refs)`"],
                        ["`print(resultado)`", "`save_result({...})`"],
                        ["excepción en pantalla", "`try` · `traceback` → `job.logs()`"],
                    ],
                    id="t",
                    stagger=True,
                    size=23,
                )
            ],
            [
                A("item", "t", at="pasos", i=0),
                A("item", "t", at="pasos", t=3, i=1),
                A("item", "t", at="pasos", t=6, i=2),
                A("item", "t", at="pasos", t=10, i=3),
                A("item", "t", at="try", i=4),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Una entrada a un programa.""",
            [Code("""job = program.run(circuits=circuits, backend=backend)""", norun=True)],
            ask=choice(
                "¿Qué problema tiene esta llamada?",
                [
                    "ninguno",
                    "`backend` debería ser el nombre (texto), porque las entradas deben ser serializables",
                    "falta `save_result`",
                ],
                1,
                'Correcto: Serverless solo acepta entradas y salidas serializables; pasa `backend_name="ibm_fez"` y crea el backend dentro del programa.',
                wrong=[
                    "El objeto backend no se puede serializar.",
                    None,
                    "`save_result` va dentro del programa, no en la llamada.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. Abre el cuaderno de práctica de esta lección con el comando de abajo. Serverless corre en la nube y pide una cuenta de pago, así que el cuaderno reproduce su contrato en tu equipo, con un backend simulado.
             [[n1]]Primero ejecutas un programa y lees sus resultados. [[n2]]Después arreglas una llamada cuyo argumento no se puede serializar. [[n3]]Y por último paralelizas con distribute task y get.
             [[check]]Cada misión tiene una comprobación que se actualiza sola mientras escribes: busca la marca verde.""",
            [
                Mission(
                    "practica/p8-serverless.py",
                    [
                        (
                            1,
                            "Ejecuta el programa y lee la profundidad transpilada de cada circuito.",
                        ),
                        (2, "Arregla la llamada: cambia la entrada que no se puede serializar."),
                        (
                            3,
                            "Paraleliza la transpilación con `distribute_task` y reúne los resultados con `get`.",
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
                "¿Por qué Serverless exige que las entradas sean serializables? Piensa en dónde corre tu programa y dónde corre tu cuaderno.",
                "Tienes un cuaderno que transpila 500 circuitos uno tras otro. ¿Qué cambiarías para llevarlo a Serverless, y qué partes dejarías secuenciales?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Un programa lee argumentos y guarda resultados. [[r2]]Se describe con QiskitFunction, se sube y se ejecuta con run. [[r3]]distribute task y get paralelizan el trabajo clásico.
             [[r4]]Y dentro del programa usa get runtime service, y el directorio de datos para tus archivos.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "serverless",
        "serverless-first-program",
        "serverless-run-first-workload",
        "serverless-manage-resources",
        "serverless-port-code",
    ],
    practice=[
        "Convierte en programa de Serverless un cuaderno tuyo que transpile 30 circuitos aleatorios y compara el tiempo con la versión local.",
        "Consulta la documentación actual en [Qiskit Serverless en GitHub](https://qiskit.github.io/qiskit-serverless/): la herramienta cambia rápido.",
    ],
)

# ------------------------------------------------------------------ 8.2 Addons
s_cierre, a_cierre = resumen(
    [
        "mapear: optimization mapper, Qiskit Fermions, AQC-Tensor, MPF",
        "optimizar circuitos: OBP, circuit cutting",
        "ruido: noise learning, SLC, PNA, Qiskit Mitigation · muestreo: SQD, M3, Paulice, postselección",
        "apoyo: addon utilities, Pauli propagation",
    ]
)
addons = lesson(
    "p8-addons",
    "Qiskit addons",
    "El catálogo de herramientas de investigación de Qiskit: qué hace cada addon y en qué paso del patrón encaja.",
    [
        "ubicar cada addon en el patrón de Qiskit",
        "elegir el addon adecuado para un problema",
        "generar un Hamiltoniano y su evolución con `qiskit-addon-utils`",
    ],
    [
        beat(
            "que",
            ("", "¿Qué son los addons?"),
            """Los addons de Qiskit son componentes de investigación para descubrir algoritmos a escala de utilidad. Son paquetes modulares que se instalan aparte y encajan en algún paso del patrón de Qiskit.
             [[cats]]Se agrupan en seis categorías: mapear problemas; optimizar circuitos para el hardware; aprender modelos de ruido; gestionar el ruido al estimar valores esperados; gestionar el ruido al muestrear; y herramientas de apoyo.""",
            [
                Flow(
                    [
                        dict(t="Mapear", s="Fermions · AQC-Tensor · MPF", color="blue"),
                        dict(t="Optimizar", s="OBP · cutting", color="violet"),
                        dict(
                            t="Ejecutar", s="noise learning · PNA · Mitigation · SLC", color="gold"
                        ),
                        dict(t="Posprocesar", s="SQD · M3 · Paulice", color="teal"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="cats", i=0),
                A("item", "f", at="cats", t=3, i=1),
                A("item", "f", at="cats", t=6, i=2),
                A("item", "f", at="cats", t=10, i=3),
            ],
        ),
        beat(
            "mapear",
            ("", "Mapear problemas"),
            """Para el primer paso, mapear. [[opt]]Optimization mapper modela problemas de optimización y los traduce a algo que entiende un computador cuántico. [[ferm]]Qiskit Fermions trabaja con sistemas fermiónicos: operadores, circuitos y codificaciones de fermiones a qubits.
             [[aqc]]AQC-Tensor construye circuitos menos profundos y de alta fidelidad con compilación aproximada mediante redes de tensores. [[mpf]]Y las fórmulas multiproducto, MPF, reducen el error de Trotter combinando con pesos varias ejecuciones.""",
            [
                Table(
                    ["Addon", "Para qué"],
                    [
                        ["Optimization mapper", "problemas de optimización → operadores"],
                        ["Qiskit Fermions", "operadores fermiónicos y codificaciones"],
                        ["AQC-Tensor", "compilación aproximada con redes de tensores"],
                        ["MPF", "menos error de Trotter combinando ejecuciones"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                )
            ],
            [
                A("item", "t", at="opt", i=0),
                A("item", "t", at="ferm", i=1),
                A("item", "t", at="aqc", i=2),
                A("item", "t", at="mpf", i=3),
            ],
        ),
        beat(
            "optimizar",
            ("", "Optimizar circuitos"),
            """Para el segundo paso hay dos herramientas que reducen la profundidad, normalmente a cambio de más muestras. [[obp]]La retropropagación de operadores, OBP, hace pasar el observable hacia atrás por el final del circuito: el circuito que se ejecuta es más corto, a cambio de un observable con más términos.
             [[cut]]Y el corte de circuitos descompone puertas entre qubits lejanos, o parte el circuito en trozos más pequeños, y recombina los resultados.""",
            [
                Row(
                    Box(
                        "def",
                        "OBP",
                        T("circuito más corto · observable más grande", "body"),
                        id="a",
                        hidden=True,
                    ),
                    Box(
                        "def",
                        "Circuit cutting",
                        T("cortar puertas lejanas · más muestras", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=24,
                )
            ],
            [A("show", "a", at="obp"), A("show", "b", at="cut")],
        ),
        beat(
            "ruido",
            ("", "Ruido"),
            """Para aprender el ruido, noise learning construye experimentos de caracterización y su análisis. Shaded lightcones, SLC, abarata la cancelación probabilística de errores quitando del modelo los términos de ruido que apenas afectan al observable.
             [[ev]]Para valores esperados: PNA, la absorción de ruido propagado, que viste en la Parte seis, y Qiskit Mitigation, para construir tus propios flujos de mitigación con Samplomatic.
             [[muestreo]]Para resultados de muestreo: SQD, la diagonalización cuántica basada en muestras, también en versión para HPC en C más más; la postselección con comprobaciones de inversión de bits; M3, mitigación de lectura en un subespacio reducido; y Paulice, comprobaciones de Pauli basadas en códigos de espacio-tiempo.""",
            [
                Table(
                    ["Objetivo", "Addons"],
                    [
                        ["aprender el ruido", "Noise learning · Shaded lightcones (SLC)"],
                        ["valores esperados", "PNA · Qiskit Mitigation"],
                        ["muestreo", "SQD (y SQD-HPC) · postselección · M3 · Paulice"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                )
            ],
            [
                A("item", "t", at="ruido", i=0),
                A("item", "t", at="ev", i=1),
                A("item", "t", at="muestreo", i=2),
            ],
        ),
        beat(
            "utils",
            ("", "Herramientas de apoyo"),
            """Por último, dos herramientas de apoyo: Pauli propagation, para aproximar la evolución de operadores, base de PNA y de SLC; y addon utilities, con utilidades para construir Hamiltonianos, circuitos de Trotter y mitigación.
             [[ej]]Probemos addon utilities: generamos un Hamiltoniano de Ising con campo transversal en una cadena de seis qubits, cinco términos ZZ y seis X, once en total.
             [[trotter]]Y su circuito de evolución temporal con dos pasos de Trotter: veinte CNOT, y rotaciones.""",
            [
                Code(
                    """from qiskit.transpiler import CouplingMap
from qiskit.synthesis import LieTrotter
from qiskit_addon_utils.problem_generators import (
    generate_xyz_hamiltonian, generate_time_evolution_circuit)

coupling_map = CouplingMap.from_line(6, bidirectional=False)
H = generate_xyz_hamiltonian(coupling_map, coupling_constants=(0.0, 0.0, 1.0),
                             ext_magnetic_field=(0.4, 0.0, 0.0))
print(H.num_qubits, len(H))
circuit = generate_time_evolution_circuit(H, synthesis=LieTrotter(reps=2), time=0.2)
print(circuit.decompose().count_ops())""",
                    id="c",
                    size=21,
                ),
                Out(
                    "6 11\nOrderedDict({'cx': 20, 'r': 12, 'rz': 10})",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="ej", range="6-9"),
                A("hl", "c", at="trotter", range="10-11"),
                A("show", "o", at="trotter", t=1),
            ],
        ),
        beat(
            "predice",
            ("", "Antes de absorber capas"),
            """Veamos la retropropagación en acción, y antes apuesta. [[circ]]Usaremos la misma cadena de seis espines de Ising, con cuatro pasos de Trotter: doce capas de puertas. [[obs]]El observable es la magnetización media: seis términos, uno por espín.
             [[abs]]Vamos a absorber las cuatro últimas capas en el observable. ¿Cuántos términos tendrá el observable nuevo? No hace falta que sepas la respuesta: equivocarse en una predicción enseña más que acertar por memoria.""",
            [
                Table(
                    ["", "antes", "después"],
                    [
                        ["capas del circuito", "12", "?"],
                        ["términos del observable", "6", "?"],
                        ["capas absorbidas", "0", "las 4 últimas"],
                    ],
                    id="t",
                    stagger=True,
                    size=26,
                )
            ],
            [
                A("item", "t", at="circ", i=0),
                A("item", "t", at="obs", i=1),
                A("item", "t", at="abs", i=2),
            ],
            ask=predict(
                "¿Cuántos términos tendrá el observable tras absorber 4 capas?",
                ["6, los mismos", "unos 12", "64", "más de mil"],
                "Anotado. Ejecutémoslo y veamos si acertaste.",
            ),
        ),
        beat(
            "obp",
            ("", "Retropropagar el observable"),
            """Este es el código. [[ej]]Construimos el circuito y lo cortamos en capas: cada capa es una columna de puertas del mismo tipo.
             [[bp]]backpropagate recibe el observable y las capas que quieres absorber, de la última a la primera, y devuelve el observable nuevo y las capas que no absorbió.
             [[res]]El resultado: de seis a sesenta y cuatro términos. El circuito pasa de profundidad doce a ocho. Y el valor esperado es el mismo, cero punto ocho dos cuatro nueve. Si apostaste por sesenta y cuatro, acertaste.
             [[costo]]Ese es el intercambio de OBP: un circuito más corto a cambio de un observable más grande, con más términos que medir.""",
            [
                Code(
                    """from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit_addon_utils.slicing import combine_slices, slice_by_gate_types
from qiskit_addon_obp import backpropagate

n = 6
circuito = QuantumCircuit(n)
for _ in range(4):
    for a in range(0, n - 1, 2):
        circuito.rzz(0.4, a, a + 1)
    for a in range(1, n - 1, 2):
        circuito.rzz(0.4, a, a + 1)
    for a in range(n):
        circuito.rx(0.2, a)

M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
capas = slice_by_gate_types(circuito)
obs, resto, meta = backpropagate(M, capas[-4:])
corto = combine_slices(capas[:-4] + list(resto), include_barriers=False)

valor = lambda c, o: Statevector(c).expectation_value(o).real
print("términos:", len(M), "->", len(obs))
print("profundidad:", circuito.depth(), "->", corto.depth())
print(f"valor: {valor(circuito, M):.4f} {valor(corto, obs):.4f}")""",
                    id="c",
                    size=17,
                ),
                Out(
                    "términos: 6 -> 64\nprofundidad: 12 -> 8\nvalor: 0.8249 0.8249",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="ej", range="6-17"),
                A("hl", "c", at="bp", range="18-19"),
                A("hl", "c", at="res", range="22-24"),
                A("show", "o", at="res", t=1),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Elige el addon.""",
            [
                T(
                    "Tu circuito de evolución temporal es demasiado profundo y solo quieres un valor esperado al final.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué addon reduce directamente la profundidad del circuito ejecutado?",
                ["M3", "OBP (retropropagación de operadores)", "SQD"],
                1,
                "Correcto: OBP absorbe las últimas capas del circuito en el observable; ejecutas un circuito más corto a cambio de medir más términos.",
                wrong=[
                    "M3 mitiga errores de lectura; no cambia el circuito.",
                    None,
                    "SQD posprocesa muestras para diagonalizar Hamiltonianos.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Abre el cuaderno de práctica de esta lección. Todo corre en tu equipo con OBP.
             [[n1]]Primero reproduces la retropropagación: cuatro capas absorbidas, sesenta y cuatro términos. [[n2]]Después le pones un presupuesto de operador, para que OBP se detenga antes de que el observable crezca demasiado. [[n3]]Y por último escribes una función que elige cuántas capas absorber dado un límite de términos.""",
            [
                Mission(
                    "practica/p8-addons.py",
                    [
                        (
                            1,
                            "Retropropaga cuatro capas y compara términos, profundidad y valor esperado.",
                        ),
                        (2, "Añade un presupuesto de operador para que OBP se detenga solo."),
                        (
                            3,
                            "Escribe `mejor_k(limite)`: cuántas capas puedes absorber sin pasar del límite de términos.",
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
            """Dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda y lo verás al volver a esta lección.""",
            [T("OBP cambia profundidad por términos que medir.", "subtitle")],
            ask=reflect(
                "OBP mueve el costo del circuito al observable. ¿Cuándo dejaría de compensar absorber más capas?",
                "Tu observable tiene un solo término Z en un qubit. ¿Crees que OBP crecería igual de rápido que con la magnetización media? ¿Por qué?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Para mapear: Fermions, AQC-Tensor, MPF. [[r2]]Para optimizar: OBP y corte de circuitos. [[r3]]Para el ruido: noise learning, PNA, Mitigation, SQD, M3 y Paulice.
             [[r4]]Y de apoyo, addon utilities y Pauli propagation.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["addons"],
    practice=[
        "Con `qiskit-addon-obp` (ya está en las dependencias del curso), absorbe las capas de un circuito de Trotter de ocho pasos y mide cuántos términos tiene el observable en cada paso.",
        "Recorre los tutoriales de [SQD](https://quantum.cloud.ibm.com/docs/en/addons/qiskit-addon-sqd) para una molécula pequeña.",
    ],
)

# ------------------------------------------------------------------ 8.3 Qiskit Functions
s_cierre, a_cierre = resumen(
    [
        "funciones de circuito (PUBs → valores mitigados) y de aplicación (datos del dominio → solución)",
        '`QiskitFunctionsCatalog` · `catalog.list()` · `catalog.load("proveedor/nombre")`',
        "`function.run(...)` · un trabajo a la vez · `status`, `result`, `logs`, `cancel`",
        "`runtime_jobs()`, `runtime_sessions()`, `catalog.jobs(...)`, `error_message()`",
    ]
)
functions = lesson(
    "p8-functions",
    "Qiskit Functions",
    "El catálogo de funciones de IBM y sus socios: qué tipos hay, cómo acceder, ejecutarlas y seguir sus trabajos.",
    [
        "distinguir funciones de circuito y de aplicación",
        "cargar y ejecutar una función del catálogo",
        "seguir, depurar y listar trabajos de funciones",
    ],
    [
        beat(
            "tipos",
            ("", "Dos tipos de funciones"),
            """Las Qiskit Functions abstraen parte del flujo de trabajo cuántico. Son experimentales, para los planes Premium, Flex y On-Prem, y las ofrecen IBM y empresas socias.
             [[circuito]]Las funciones de circuito reciben PUBs abstractos y devuelven valores esperados mitigados: se encargan de transpilar, suprimir y mitigar errores. Son para investigadores que quieren centrarse en el algoritmo.
             [[aplicacion]]Las funciones de aplicación reciben datos del dominio, como moléculas o grafos, y devuelven respuestas del dominio, como energías u óptimos. Son para expertos de otras áreas que quieren integrar computación cuántica sin traducir sus datos a circuitos.""",
            [
                Row(
                    Box(
                        "def",
                        "Función de circuito",
                        T("PUBs abstractos → valores esperados mitigados", "body"),
                        id="a",
                        hidden=True,
                    ),
                    Box(
                        "idea",
                        "Función de aplicación",
                        T("moléculas, grafos → energías, óptimos", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=24,
                )
            ],
            [A("show", "a", at="circuito"), A("show", "b", at="aplicacion")],
        ),
        beat(
            "acceso",
            ("", "Acceder al catálogo"),
            """Las funciones de IBM se pueden usar directamente; las de terceros requieren una licencia o una prueba gratuita, que se pide desde el catálogo indicando el identificador de tu grupo de acceso de IBM Cloud.
             [[instalar]]Se instala qiskit ibm catalog. [[cuenta]]Igual que con el servicio de Runtime, guardas tu cuenta una vez con save account, en un entorno de confianza, y después basta con QiskitFunctionsCatalog. La instancia debe tener habilitado el acceso a Functions.
             [[clave]]Y lo de siempre: nunca pongas tu clave de API en el código.""",
            [
                Code(
                    """from qiskit_ibm_catalog import QiskitFunctionsCatalog

QiskitFunctionsCatalog.save_account(channel="ibm_quantum_platform",
                                    token="<tu-clave>", instance="<crn>")   # una vez
catalog = QiskitFunctionsCatalog(channel="ibm_quantum_platform")
catalog.list()""",
                    id="c",
                    norun=True,
                    size=22,
                ),
                Out(
                    """[QiskitFunction(qunova/hivqe-chemistry),
 QiskitFunction(algorithmiq/tem),
 QiskitFunction(qedma/qesem),
 QiskitFunction(ibm/circuit-function),
 QiskitFunction(q-ctrl/optimization-solver), ...]""",
                    id="o",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="cuenta", range="3-5"),
                A("hl", "c", at="clave", range="3-4"),
                A("show", "o", at="clave", t=3),
            ],
        ),
        beat(
            "predice",
            ("", "Antes de ejecutar"),
            """Una apuesta antes de ejecutar. [[carga]]Cargas la función QESEM. [[run]]Y la ejecutas nombrando un backend al que tu instancia no tiene acceso. [[pregunta]]¿Qué crees que hace run?""",
            [
                Code(
                    """qesem = catalog.load("qedma/qesem")
job = qesem.run(
    pubs=[(circuit, [avg_magnetization])],
    backend_name="ibm_inexistente",   # tu instancia no lo ve
)""",
                    id="c",
                    norun=True,
                    size=23,
                )
            ],
            [A("hl", "c", at="carga", lines=[1]), A("hl", "c", at="run", range="2-5")],
            ask=predict(
                "Nombras un backend al que tu instancia no tiene acceso. ¿Qué hace `run`?",
                [
                    "lo envía y el trabajo falla después, en la cola",
                    "falla enseguida, con un error",
                    "elige otro backend por ti",
                    "espera hasta que tengas acceso",
                ],
                "Anotado. En el siguiente paso lo vemos.",
            ),
        ),
        beat(
            "ejecutar",
            ("", "Ejecutar una función"),
            """Cargas una función con catalog punto load y su nombre, proveedor barra nombre. [[run]]Cada función tiene sus propias entradas y opciones; esta, QESEM de Qedma, recibe PUBs y el nombre del backend.
             [[uno]]Por defecto solo puedes tener un trabajo de función en ejecución a la vez. [[capacidad]]Esta es la respuesta a tu apuesta: antes de enviarlo, run comprueba tu capacidad restante y el acceso al backend, y falla enseguida si algo no está bien, en vez de dejar que el trabajo falle en la cola.""",
            [
                Code(
                    """qesem = catalog.load("qedma/qesem")
job = qesem.run(
    pubs=[(circuit, [avg_magnetization, observable])],
    backend_name="ibm_fez",
)
print(job.job_id)""",
                    id="c",
                    norun=True,
                    size=23,
                )
            ],
            [A("hl", "c", at="ejecutar", lines=[1]), A("hl", "c", at="run", range="2-5")],
        ),
        beat(
            "estado",
            ("", "Estados del trabajo"),
            """Los estados son los de Serverless: en cola, con prioridad según cuánto hayas usado Functions; inicializando; ejecutándose, con los subestados de mapeo, optimización, espera y ejecución en el QPU, y posprocesamiento; y terminado.
             [[error]]Además, error, si algo falló, y cancelado.""",
            [
                Flow(
                    [
                        dict(t="QUEUED"),
                        dict(t="INITIALIZING"),
                        dict(
                            t="RUNNING",
                            s="MAPPING · OPTIMIZING · WAITING_QPU · EXECUTING_QPU · POST_PROCESSING",
                            color="gold",
                        ),
                        dict(t="DONE", color="teal"),
                    ],
                    id="f",
                    stagger=True,
                ),
                T(
                    "también: `ERROR` (mira `job.error_message()`) · `CANCELED`",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("item", "f", at="estado", i=0),
                A("item", "f", at="estado", t=2, i=1),
                A("item", "f", at="estado", t=3, i=2),
                A("item", "f", at="estado", t=8, i=3),
                A("show", "n", at="error"),
            ],
        ),
        beat(
            "seguir",
            ("", "Seguir y depurar"),
            """Para seguir un trabajo: status, result y cancel, como siempre. [[rt]]Una función lanza sus propios trabajos de Runtime; runtime jobs te da sus identificadores, y runtime sessions las sesiones o lotes que agrupó.
             [[logs]]logs te da los registros, y filtered logs, solo las líneas que coinciden con una expresión regular. [[jobs]]catalog punto jobs lista tus trabajos, con filtros por función, estado o fecha, y catalog punto job recupera uno por su identificador. [[err]]Si terminó en error, error message te dice por qué.""",
            [
                Code(
                    """job.status(); job.result(); job.cancel()
job.runtime_jobs()                          # IDs de los trabajos de Runtime
job.runtime_sessions()
print(job.filtered_logs(include="iteration"))
catalog.jobs(function=qesem, status="ERROR", created_after="2024-01-01T00:00:00Z", limit=5)
catalog.job(job_id)
job.error_message()""",
                    id="c",
                    norun=True,
                    size=21,
                )
            ],
            [
                A("hl", "c", at="seguir", lines=[1]),
                A("hl", "c", at="rt", range="2-3"),
                A("hl", "c", at="logs", lines=[4]),
                A("hl", "c", at="jobs", range="5-6"),
                A("hl", "c", at="err", lines=[7]),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Elige el tipo de función.""",
            [
                T(
                    "Una química quiere la energía del estado fundamental de una molécula y no sabe nada de circuitos.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué tipo de función le conviene?",
                ["de circuito", "de aplicación", "ninguna: tiene que escribir el circuito"],
                1,
                "Correcto: una función de aplicación (por ejemplo, HI-VQE de Qunova) recibe la geometría de la molécula y devuelve energías.",
                wrong=[
                    "Una función de circuito necesita que ya tengas circuitos y observables.",
                    None,
                    "Precisamente para eso existen las funciones de aplicación.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Abre el cuaderno de práctica de esta lección. Las funciones piden un plan de pago, así que el cuaderno trae un catálogo local con la misma interfaz, y nada sale de tu equipo.
             [[n1]]Primero listas el catálogo, cargas una función, la ejecutas y sigues sus estados. [[n2]]Después arreglas un backend al que no tienes acceso. [[n3]]Y por último escribes una función que resume un trabajo: sus estados, sus trabajos de Runtime, sus registros y su error.""",
            [
                Mission(
                    "practica/p8-functions.py",
                    [
                        (1, "Lista el catálogo, carga una función, ejecútala y sigue sus estados."),
                        (
                            2,
                            "Arregla el backend: cambia el nombre por uno al que tu instancia tiene acceso.",
                        ),
                        (
                            3,
                            "Escribe `resumen(job)`: los estados que recorre, sus trabajos de Runtime, sus registros y su error.",
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
            """Dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda y lo verás al volver a esta lección.""",
            [T("Fallar enseguida cuesta menos que fallar en la cola.", "subtitle")],
            ask=reflect(
                "¿Por qué conviene que `run` valide el acceso al backend antes de enviar el trabajo, en lugar de dejar que falle en la cola?",
                "Tu trabajo lleva horas en `RUNNING` y quieres saber qué pasa. ¿Qué métodos del trabajo usarías, en qué orden, y qué esperas encontrar en cada uno?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Funciones de circuito y de aplicación. [[r2]]Se accede con QiskitFunctionsCatalog y se cargan por nombre. [[r3]]Se ejecutan con run, un trabajo a la vez.
             [[r4]]Y se siguen con status, logs, runtime jobs y error message.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["functions", "functions-get-started"],
    practice=[
        "Abre el [catálogo de funciones](https://quantum.cloud.ibm.com/functions) y lee la ficha de una función de circuito y una de aplicación.",
        "Si tienes plan Premium, ejecuta `ibm/circuit-function` con un circuito pequeño y revisa sus `runtime_jobs()`.",
    ],
)

# ------------------------------------------------------------------ 8.4 Funciones de circuito
s_cierre, a_cierre = resumen(
    [
        "TEM (Algorithmiq): mitigación en posprocesamiento con redes de tensores y medidas IC",
        "QESEM (Qedma): valores sin sesgo con precisión garantizada · estimación de tiempo previa",
        "Performance Management (Q-CTRL): supresión automática con IA · Sampler y Estimator",
        "Orbit (Quantum Elements): transpilación, DD y mitigación de lectura · modos `raw`/`orbit`",
    ]
)
circuit_functions = lesson(
    "p8-circuit-functions",
    "Funciones de circuito",
    "Las cuatro funciones de circuito del catálogo: TEM, QESEM, Performance Management y Orbit: qué hacen, cuándo convienen y cómo se llaman.",
    [
        "comparar las cuatro funciones de circuito",
        "elegir una según el tipo de circuito y observable",
        "conocer sus entradas y salidas típicas",
    ],
    [
        beat(
            "panorama",
            ("", "Cuatro funciones de circuito"),
            """Las funciones de circuito sustituyen a las primitivas: reciben PUBs y se encargan de transpilar, suprimir y mitigar. Hay cuatro en el catálogo, cada una con sus puntos fuertes.""",
            [
                Table(
                    ["Función", "Proveedor", "Mejor para"],
                    [
                        ["TEM", "Algorithmiq", "observables de bajo peso, circuitos sin bucles"],
                        [
                            "QESEM",
                            "Qedma",
                            "puertas fraccionales, observables de alto peso, resultados sin sesgo",
                        ],
                        [
                            "Performance Management",
                            "Q-CTRL",
                            "circuitos paramétricos o profundos, muchas ejecuciones",
                        ],
                        [
                            "Orbit",
                            "Quantum Elements",
                            "tiempos ociosos, circuitos dinámicos, corrección de errores",
                        ],
                    ],
                    id="t",
                    stagger=True,
                    size=22,
                )
            ],
            [
                A("item", "t", at="panorama", t=4, i=0),
                A("item", "t", at="panorama", t=5, i=1),
                A("item", "t", at="panorama", t=6, i=2),
                A("item", "t", at="panorama", t=7, i=3),
            ],
        ),
        beat(
            "tem",
            ("", "TEM, de Algorithmiq"),
            """TEM, mitigación de errores con redes de tensores, mitiga el ruido completamente en el posprocesamiento clásico. Mide el circuito con una medición informacionalmente completa, y construye una red de tensores que representa la inversa del canal de ruido global.
             [[ventajas]]Sus ventajas: un sobrecosto de mediciones óptimo según las cotas teóricas; no añade circuitos extra al QPU; muchos observables con los mismos datos; e incluye su propia mitigación de lectura.
             [[uso]]Se llama con PUBs, el backend, y opciones como la precisión deseada.""",
            [
                Code(
                    """tem = catalog.load("algorithmiq/tem")
pub = (qc, [SparsePauliOp("IYX")])
job = tem.run(pubs=[pub], backend_name="ibm_marrakesh",
              options={"default_precision": 0.02})""",
                    id="c",
                    norun=True,
                    size=23,
                ),
                L(
                    [
                        "sobrecosto de medición óptimo",
                        "sin circuitos extra en el QPU",
                        "muchos observables con los mismos datos",
                        "mitigación de lectura incluida",
                    ],
                    id="l",
                    stagger=True,
                ),
            ],
            [
                A("item", "l", at="ventajas", i=0),
                A("item", "l", at="ventajas", t=4, i=1),
                A("item", "l", at="ventajas", t=7, i=2),
                A("item", "l", at="ventajas", t=10, i=3),
                A("hl", "c", at="uso", range="3-4"),
            ],
        ),
        beat(
            "predice",
            ("", "Antes de QESEM"),
            """Antes de ver QESEM, una apuesta. QESEM te deja elegir la precisión que quieres: el error máximo de tu estimación. [[hoy]]Imagina que con un error de cero punto cero dos el trabajo tarda diez minutos de QPU. [[mitad]]Ahora pides la mitad del error: cero punto cero uno. [[pregunta]]¿Cuánto tarda?""",
            [
                Table(
                    ["Error pedido", "Tiempo de QPU"],
                    [["0.02", "10 min"], ["0.01", "?"]],
                    id="t",
                    stagger=True,
                    size=30,
                )
            ],
            [A("item", "t", at="hoy", i=0), A("item", "t", at="mitad", i=1)],
            ask=predict(
                "Pides la mitad de error a QESEM. ¿Cuánto crece el tiempo de QPU?",
                ["se reduce a la mitad", "el doble", "el cuádruple", "no cambia"],
                "Anotado. Ahora veamos cómo es el costo de QESEM.",
            ),
        ),
        beat(
            "qesem",
            ("", "QESEM, de Qedma"),
            """QESEM produce estimaciones sin sesgo, con garantías teóricas, hasta la precisión que pidas. Para ello caracteriza el dispositivo para tu circuito, transpila teniendo en cuenta el ruido, y aplica supresión y mitigación.
             [[tiempo]]Esta es la respuesta a tu apuesta: su sobrecosto de QPU crece con el inverso del cuadrado de la precisión, así que la mitad del error cuesta cuatro veces más tiempo. Y crece exponencialmente con el volumen activo del circuito, el número de puertas de dos qubits que afectan al observable.
             [[estimar]]Por eso tiene un modo para estimar el tiempo antes de gastar: estimate time only. Con un backend simulado, como fake fez, no gasta QPU.""",
            [
                M(r"T_{QPU}\approx a\,\frac{e^{\alpha\,IF\cdot V_a}}{\epsilon^2}+b", size=44),
                Code(
                    """job = qesem.run(pubs=[(circ, [avg_magnetization])],
                options={"estimate_time_only": "empirical"},
                backend_name="fake_fez")
job.result()[0].metadata["time_estimation_sec"]""",
                    id="c",
                    hidden=True,
                    norun=True,
                    size=22,
                ),
            ],
            [A("show", "c", at="estimar")],
        ),
        beat(
            "qctrl",
            ("", "Performance Management, de Q-CTRL"),
            """Performance Management, de Fire Opal, aplica automáticamente supresión de errores guiada por IA, sin configuración. No añade tiempo de QPU ni qubits extra: a diferencia de la mitigación, evita que los errores ocurran.
             [[primitivas]]Ofrece dos primitivas, Sampler y Estimator, compatibles con las de IBM: solo cambias quién las ejecuta.
             [[bench]]En sus pruebas en Fez: Bernstein-Vazirani con cincuenta qubits y transformada de Fourier con treinta, con cien por ciento de éxito.""",
            [
                Code(
                    """perf_mgmt = catalog.load("q-ctrl/performance-management")
job = perf_mgmt.run(primitive="estimator", pubs=estimator_pubs, backend_name="ibm_fez")
job = perf_mgmt.run(primitive="sampler", pubs=sampler_pubs, backend_name="ibm_fez")""",
                    id="c",
                    norun=True,
                    size=21,
                ),
                Table(
                    ["Ejemplo", "Qubits", "Éxito"],
                    [["Bernstein-Vazirani", "50", "100 %"], ["QFT", "30", "100 %"]],
                    id="t",
                    hidden=True,
                    size=23,
                ),
            ],
            [A("hl", "c", at="primitivas", range="2-3"), A("show", "t", at="bench")],
        ),
        beat(
            "orbit",
            ("", "Orbit, de Quantum Elements"),
            """Orbit combina tres técnicas: transpilación optimizada, desacoplamiento dinámico y mitigación de errores de lectura. Brilla en circuitos con periodos ociosos, como los dinámicos con mediciones a mitad del circuito o la corrección de errores.
             [[modos]]No es una caja negra: puedes activar o desactivar cada componente y comparar configuraciones. Por ejemplo, el mismo circuito en modo raw, sin Orbit, como referencia, y en modo orbit.
             [[bench]]En una transformada de Fourier dinámica de diez qubits, la fidelidad pasó de un dos por ciento a cerca de un cincuenta y cinco.""",
            [
                Code(
                    """orbit = catalog.load("quantum-elements/orbit")
job = orbit.run(
    primitive="sampler", pubs=pubs, backend_name="ibm_kingston",
    options={"pub_options": [{"mode": "raw"}, {"mode": "orbit"}]},
)""",
                    id="c",
                    norun=True,
                    size=22,
                ),
                Hist(
                    [["raw", 2], ["Orbit", 55]],
                    id="h",
                    hidden=True,
                    h=110,
                    ymax=60,
                    digits=0,
                    ylabel="fidelidad QFT dinámica %",
                    color="teal",
                ),
            ],
            [A("hl", "c", at="modos", lines=[4]), A("show", "h", at="bench")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Elige la función.""",
            [
                T(
                    "Necesitas un valor esperado sin sesgo con una precisión garantizada, y quieres saber antes cuánto tiempo de QPU costará.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué función encaja mejor?",
                ["Orbit", "QESEM", "Performance Management"],
                1,
                "Correcto: QESEM da resultados sin sesgo con precisión elegida, y su modo `estimate_time_only` estima el tiempo de QPU antes de ejecutar.",
                wrong=[
                    "Orbit suprime errores, pero no garantiza un resultado sin sesgo.",
                    None,
                    "Performance Management suprime errores; no estima tiempos ni garantiza sesgo cero.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Abre el cuaderno de práctica de esta lección. Corre con primitivas locales; no usa ninguna cuenta.
             [[n1]]Primero mides cómo baja el error de un estimador al subir su precisión. [[n2]]Después arreglas una fórmula de tiempo de QPU cuyo exponente está mal. [[n3]]Y por último inviertes la fórmula: dado un tiempo máximo, calculas qué precisión puedes pedir.""",
            [
                Mission(
                    "practica/p8-circuit-functions.py",
                    [
                        (
                            1,
                            "Ejecuta el estimador con varias precisiones y mide cómo cambia la dispersión.",
                        ),
                        (2, "Arregla el exponente de la fórmula del tiempo de QPU."),
                        (3, "Escribe `precision_alcanzable(t_max, va)`: la inversa de la fórmula."),
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
            """Dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda y lo verás al volver a esta lección.""",
            [T("Pedir más precisión sale caro: el costo crece con el cuadrado.", "subtitle")],
            ask=reflect(
                "Si el costo crece con el inverso del cuadrado de la precisión, ¿cómo decidirías qué error te puedes permitir en un experimento con presupuesto de QPU limitado?",
                "Tienes un circuito de Trotter profundo y un observable de alto peso. ¿Qué función de circuito elegirías y por qué?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]TEM mitiga en posprocesamiento con redes de tensores. [[r2]]QESEM da valores sin sesgo y estima su costo. [[r3]]Performance Management suprime errores automáticamente.
             [[r4]]Y Orbit combina transpilación, desacoplamiento y mitigación de lectura.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "algorithmiq-tem",
        "q-ctrl-performance-management",
        "qedma-qesem",
        "quantum-elements-orbit",
    ],
    practice=[
        "Lee la sección de benchmarks de cada función y anota qué tamaño de circuito manejan.",
        "Si tienes acceso, compara en un mismo circuito el resultado de Estimator con `resilience_level=2` y el de una función de circuito.",
    ],
)

# ------------------------------------------------------------------ 8.5 Funciones de aplicación
s_cierre, a_cierre = resumen(
    [
        "optimización: Iskay (Kipu), Optimization Solver (Q-CTRL), Parity Twine, Constrained Optimizer (Aqarios)",
        "finanzas: Quantum Portfolio Optimizer (Global Data Quantum)",
        "química y física: HI-VQE (Qunova), QUICK-PDE (ColibriTD)",
        "aprendizaje automático: Singularity (Multiverse Computing)",
    ]
)
app_functions = lesson(
    "p8-app-functions",
    "Funciones de aplicación",
    "Las funciones de aplicación del catálogo: optimización, finanzas, química, ecuaciones diferenciales y aprendizaje automático.",
    [
        "conocer las funciones de aplicación disponibles",
        "saber qué entradas recibe cada una",
        "elegir la adecuada para un problema del dominio",
    ],
    [
        beat(
            "panorama",
            ("", "Panorama"),
            """Las funciones de aplicación reciben datos del dominio y devuelven soluciones del dominio. Hay ocho en el catálogo. La mitad se dedica a optimización.""",
            [
                Table(
                    ["Función", "Proveedor", "Dominio"],
                    [
                        ["Iskay Quantum Optimizer", "Kipu Quantum", "optimización QUBO / HUBO"],
                        ["Optimization Solver", "Q-CTRL", "optimización binaria"],
                        ["Parity Twine Optimizer", "ParityQC", "optimización con menos puertas"],
                        [
                            "Constrained Quantum Optimizer",
                            "Aqarios",
                            "optimización con restricciones",
                        ],
                        ["Quantum Portfolio Optimizer", "Global Data Quantum", "finanzas"],
                        ["HI-VQE Chemistry", "Qunova", "química"],
                        ["QUICK-PDE", "ColibriTD", "ecuaciones diferenciales"],
                        ["Singularity", "Multiverse Computing", "clasificación"],
                    ],
                    id="t",
                    stagger=True,
                    size=20,
                )
            ],
            [
                A("item", "t", at="panorama", t=0, i=0),
                A("item", "t", at="panorama", t=1, i=1),
                A("item", "t", at="panorama", t=2, i=2),
                A("item", "t", at="panorama", t=3, i=3),
                A("item", "t", at="panorama", t=4, i=4),
                A("item", "t", at="panorama", t=5, i=5),
                A("item", "t", at="panorama", t=6, i=6),
                A("item", "t", at="panorama", t=7, i=7),
            ],
        ),
        beat(
            "optim",
            ("", "Optimización"),
            """Cuatro optimizadores. [[iskay]]Iskay, de Kipu, usa el algoritmo bf-DCQO, no variacional: términos contradiabáticos que comprimen el circuito, un campo de sesgo que se actualiza en cada iteración y una búsqueda local clásica al final. Admite problemas cuadráticos y de orden superior, HUBO.
             [[qctrl]]El Optimization Solver de Q-CTRL acepta una función objetivo polinómica, un grafo de networkx o un SparsePauliOp, y automatiza todo, con supresión de errores incluida; por ejemplo, máximo corte en un grafo de ciento cincuenta y seis nodos.
             [[parity]]Parity Twine usa la arquitectura de paridad para implementar interacciones no locales sin puertas SWAP, reduciendo la profundidad de QAOA.
             [[aqarios]]Y el de Aqarios resuelve problemas con restricciones, dados como archivos LP o MPS: impone las restricciones one-hot con mezcladores XY, en lugar de penalizaciones. Solo variables discretas.""",
            [
                Code(
                    """iskay = catalog.load("kipu-quantum/iskay-quantum-optimizer")
solver = catalog.load("q-ctrl/optimization-solver")
job = solver.run(problem=problem_as_str, problem_type="maxcut", backend_name="ibm_fez")
twine = catalog.load("parityqc/parity-twine-optimizer")
job = twine.run(problem={"()": 3, "(0,)": 1, "(0, 1)": 2, "(1, 2)": -1},
                variable_type="binary", backend_name="ibm_fez")
aqarios = catalog.load("aqarios/constrained-quantum-optimizer")
job = aqarios.run(problem=lp_str, backend_name="ibm_fez", options=options)""",
                    id="c",
                    norun=True,
                    size=19,
                )
            ],
            [
                A("hl", "c", at="iskay", lines=[1]),
                A("hl", "c", at="qctrl", range="2-3"),
                A("hl", "c", at="parity", range="4-6"),
                A("hl", "c", at="aqarios", range="7-8"),
            ],
        ),
        beat(
            "predice",
            ("", "Antes de finanzas"),
            """Una apuesta antes de pasar a finanzas. El Quantum Portfolio Optimizer codifica cada decisión de inversión con varios qubits. [[datos]]En el ejemplo de la guía hay siete activos, [[pasos]]cuatro pasos de tiempo, [[res]]y cuatro qubits de resolución por cada decisión. [[pregunta]]¿Cuántos qubits necesita el problema entero?""",
            [
                Table(
                    ["Dato", "Valor"],
                    [
                        ["activos", "7"],
                        ["pasos de tiempo", "4"],
                        ["qubits de resolución por decisión", "4"],
                        ["qubits en total", "?"],
                    ],
                    id="t",
                    stagger=True,
                    size=28,
                )
            ],
            [
                A("item", "t", at="datos", i=0),
                A("item", "t", at="pasos", i=1),
                A("item", "t", at="res", i=2),
                A("item", "t", at="pregunta", i=3),
            ],
            ask=predict(
                "7 activos, 4 pasos de tiempo y 4 qubits de resolución. ¿Cuántos qubits necesita el problema?",
                ["15", "28", "112", "448"],
                "Anotado. En el siguiente paso ves cómo se obtiene.",
            ),
        ),
        beat(
            "finanzas",
            ("", "Finanzas"),
            """El Quantum Portfolio Optimizer resuelve la optimización dinámica de carteras: redistribuir periódicamente una inversión entre varios activos para maximizar el rendimiento y minimizar el riesgo.
             [[como]]Formula el problema como QUBO, lo convierte en un Hamiltoniano de Ising y lo resuelve con VQE. [[ej]]Esta es la respuesta a tu apuesta: siete activos por cuatro pasos de tiempo por cuatro qubits de resolución son ciento doce qubits. Se multiplican, no se suman.""",
            [
                Flow(
                    [
                        dict(t="precios de activos"),
                        dict(t="QUBO → Ising"),
                        dict(t="VQE", color="gold"),
                        dict(t="cartera óptima", color="teal"),
                    ],
                    id="f",
                    stagger=True,
                ),
                M(
                    r"7\ \text{activos}\times 4\ \text{pasos}\times 4\ \text{qubits}=112\ \text{qubits}",
                    size=36,
                    id="m",
                    hidden=True,
                ),
            ],
            [
                A("item", "f", at="finanzas", i=0),
                A("item", "f", at="como", i=1),
                A("item", "f", at="como", t=3, i=2),
                A("item", "f", at="como", t=5, i=3),
                A("show", "m", at="ej"),
            ],
        ),
        beat(
            "ciencia",
            ("", "Química y ecuaciones diferenciales"),
            """HI-VQE, de Qunova, estima el estado fundamental de moléculas. Usa el circuito cuántico para encontrar las configuraciones electrónicas más relevantes, y diagonaliza el Hamiltoniano clásicamente en ese subespacio, que se refina en cada iteración. Recibe la geometría de la molécula.
             [[pde]]QUICK-PDE, de ColibriTD, resuelve ecuaciones en derivadas parciales con un algoritmo variacional: codifica la solución como combinación de polinomios de Chebyshev, dos a la n para n qubits. Incluye casos de dinámica de fluidos, como la ecuación de Burgers, y de dinámica de materiales.""",
            [
                Code(
                    """hivqe = catalog.load("qunova/hivqe-chemistry")
job = hivqe.run(geometry=geometry, backend_name="ibm_marrakesh", max_states=2000, ...)
quick = catalog.load("colibritd/quick-pde")
job = quick.run(use_case="CFD_BURGER", physical_parameters={"a": 1.0, "b": 0.0})""",
                    id="c",
                    norun=True,
                    size=21,
                ),
                M(
                    r"\frac{\partial u}{\partial t}+u\frac{\partial u}{\partial x}=0",
                    size=40,
                    id="m",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="ciencia", range="1-2"),
                A("hl", "c", at="pde", range="3-4"),
                A("show", "m", at="pde", t=6),
            ],
        ),
        beat(
            "ml",
            ("", "Aprendizaje automático"),
            """Singularity, de Multiverse Computing, es un clasificador híbrido de conjunto. Entrena clásicamente muchos clasificadores, como árboles de decisión o vecinos cercanos, y usa optimización cuántica para elegir la combinación más diversa y que mejor generaliza.
             [[escala]]El número de qubits solo limita el tamaño del conjunto, no el del conjunto de datos, que puede tener millones de ejemplos. [[acciones]]Se usa con acciones: create, fit, predict, y list.""",
            [
                Code(
                    """singularity = catalog.load("multiverse/singularity")
singularity.run(action="create", name="my_classifier", num_learners=10,
                learners_types=["DecisionTreeClassifier", "KNeighborsClassifier"],
                learners_proportions=[0.5, 0.5])
singularity.run(action="fit", name="my_classifier", X="X_train.npy", y="y_train.npy")
singularity.run(action="predict", name="my_classifier", X="X_test.npy")""",
                    id="c",
                    norun=True,
                    size=20,
                )
            ],
            [A("hl", "c", at="acciones", range="2-6")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Elige la función.""",
            [
                T(
                    "Debes asignar turnos: cada trabajador cubre exactamente un turno (restricción one-hot). El problema está en un archivo LP.",
                    "body",
                )
            ],
            ask=choice(
                "¿Cuál encaja mejor?",
                ["Singularity", "Constrained Quantum Optimizer (Aqarios)", "QUICK-PDE"],
                1,
                "Correcto: recibe archivos LP y impone las restricciones one-hot de forma nativa con mezcladores XY.",
                wrong=[
                    "Singularity clasifica datos.",
                    None,
                    "QUICK-PDE resuelve ecuaciones diferenciales.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Abre el cuaderno de práctica de esta lección. Las funciones de aplicación piden problemas en el formato del dominio; aquí los resuelves tú, en tu equipo, sin cuenta.
             [[n1]]Primero resuelves un máximo corte, con el diccionario QUBO de Parity Twine. [[n2]]Después arreglas una cartera que debe elegir exactamente dos activos: la penalización es demasiado pequeña. [[n3]]Y por último escribes la conversión de QUBO a Hamiltoniano de Ising, y la compruebas contra las dieciséis energías.""",
            [
                Mission(
                    "practica/p8-app-functions.py",
                    [
                        (
                            1,
                            "Resuelve un máximo corte con el diccionario QUBO y busca el mejor corte.",
                        ),
                        (
                            2,
                            "Sube la penalización para que la cartera elija exactamente dos activos.",
                        ),
                        (
                            3,
                            "Escribe `qubo_a_ising`: convierte x = (1 − Z)/2 y comprueba las energías.",
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
            """Dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda y lo verás al volver a esta lección.""",
            [T("Una función de aplicación esconde el circuito, pero no el problema.", "subtitle")],
            ask=reflect(
                "En la misión de la cartera, una penalización muy pequeña dio una solución que rompía la restricción. ¿Por qué la penalización no puede ser un número cualquiera?",
                "Una función de aplicación te evita escribir el circuito. ¿Qué pierdes y qué ganas al usarla en lugar de armar tu propio flujo con primitivas?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Cuatro optimizadores: Iskay, Q-CTRL, Parity Twine y Aqarios. [[r2]]Finanzas con el Portfolio Optimizer. [[r3]]Química con HI-VQE y ecuaciones diferenciales con QUICK-PDE.
             [[r4]]Y clasificación con Singularity.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "kipu-optimization",
        "multiverse-computing-singularity",
        "q-ctrl-optimization-solver",
        "global-data-quantum-optimizer",
        "colibritd-pde",
        "qunova-chemistry",
        "aqarios-constrained-quantum-optimizer",
        "parity-twine-optimizer",
    ],
    practice=[
        "Formula como diccionario QUBO un problema de máximo corte de 4 nodos, en el formato de Parity Twine.",
        "Lee la sección de benchmarks de Iskay y compara su número de puertas con QAOA estándar.",
    ],
)

# ------------------------------------------------------------------ 8.6 Plantillas
s_cierre, a_cierre = resumen(
    [
        "plantillas de implementación: química (SQD + IEF-PCM), simulación Hamiltoniana, AQC + Trotter",
        "plantillas base: función de circuito y de aplicación (buenas prácticas)",
        "se despliegan en tu cuenta de Serverless: `QiskitFunction(..., dependencies=[...])`",
        "validar entradas al principio · probar en `statevector` o `fake` antes de `runtime`",
    ]
)
plantillas = lesson(
    "p8-plantillas",
    "Plantillas de Qiskit Functions",
    "Plantillas de código abierto con flujos de investigación reales, y plantillas base para escribir tus propias funciones y desplegarlas en Serverless.",
    [
        "distinguir plantillas de implementación y base",
        "desplegar una plantilla en tu cuenta de Serverless",
        "aplicar las buenas prácticas de diseño de funciones",
    ],
    [
        beat(
            "que",
            ("", "¿Qué son las plantillas?"),
            """Las plantillas de Qiskit Functions son ejemplos de código abierto que empaquetan flujos de investigación reales para que los ejecutes en tu cuenta de Serverless.
             [[impl]]Las plantillas de implementación aplican técnicas avanzadas de experimentos reales: hoy, una de química y dos de física. [[base]]Las plantillas base son referencias para escribir tu propia función, de circuito o de aplicación: diseño de la interfaz, entradas y salidas, mensajes de error, puntos de control y pruebas unitarias.""",
            [
                Row(
                    Box(
                        "def",
                        "Implementación",
                        T(
                            "química: SQD + solvente implícito · física: simulación Hamiltoniana, AQC + Trotter",
                            "body",
                        ),
                        id="a",
                        hidden=True,
                    ),
                    Box(
                        "idea",
                        "Base",
                        T("función de circuito · función de aplicación · buenas prácticas", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=24,
                )
            ],
            [A("show", "a", at="impl"), A("show", "b", at="base")],
        ),
        beat(
            "quimica",
            ("", "Química con solvente implícito"),
            """La plantilla de química, desarrollada con la Cleveland Clinic, calcula la energía del estado fundamental y la energía libre de solvatación de una molécula en un solvente, modelado como un medio dieléctrico continuo, el modelo IEF-PCM. Por ejemplo, metanol en agua.
             [[pasos]]Sigue el patrón de Qiskit: prepara los datos con PySCF y construye un circuito LUCJ con amplitudes de un cálculo CCSD; lo transpila; lo ejecuta con Sampler; y posprocesa los bits con SQD.""",
            [
                Flow(
                    [
                        dict(t="Mapear", s="PySCF · CCSD → LUCJ", color="blue"),
                        dict(t="Optimizar", s="transpilar a ISA", color="violet"),
                        dict(t="Ejecutar", s="Sampler", color="gold"),
                        dict(t="Posprocesar", s="SQD + IEF-PCM", color="teal"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="pasos", i=0),
                A("item", "f", at="pasos", t=4, i=1),
                A("item", "f", at="pasos", t=5, i=2),
                A("item", "f", at="pasos", t=6, i=3),
            ],
        ),
        beat(
            "hamiltoniano",
            ("", "Simulación Hamiltoniana con AQC-Tensor"),
            """La plantilla de simulación Hamiltoniana muestra cómo construir una función. Recibe un Hamiltoniano, un estado inicial y observables, y devuelve valores esperados tras la evolución temporal.
             [[validar]]Primero lee y valida todas las entradas, al principio, para fallar pronto si falta algo. [[aqc]]Después usa AQC-Tensor: comprime las primeras capas del circuito de Trotter en un ansatz más corto, optimizado con estados de producto de matrices hasta una fidelidad objetivo. [[ejec]]Por último, añade el resto de la evolución, transpila y ejecuta con Estimator y mitigación.""",
            [
                Flow(
                    [
                        dict(t="validar entradas", s="fallar pronto"),
                        dict(t="AQC-Tensor", s="comprimir capas iniciales (MPS)", color="violet"),
                        dict(t="resto de Trotter"),
                        dict(t="Estimator", s="con mitigación", color="teal"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="validar", i=0),
                A("item", "f", at="aqc", i=1),
                A("item", "f", at="ejec", i=2),
                A("item", "f", at="ejec", t=3, i=3),
            ],
        ),
        beat(
            "predice",
            ("", "Antes de desplegar"),
            """Una apuesta sobre la plantilla de AQC más Trotter. [[total]]Pides diez pasos de Trotter en total. [[plan]]Y un plan de compresión: seis de esos pasos se comprimen en un ansatz de dos capas. Los pasos que quedan se ejecutan sin comprimir. [[pregunta]]¿Cuántas capas de Trotter tendrá el circuito del último paso?""",
            [
                Code(
                    """job = fn.run(hamiltonian=H, t_steps=10,
             aqc_segments=[{"n_steps": 6, "ansatz_steps": 2}],
             backend="statevector")""",
                    id="c",
                    norun=True,
                    size=24,
                )
            ],
            [A("hl", "c", at="total", lines=[1]), A("hl", "c", at="plan", lines=[2])],
            ask=predict(
                "¿Cuántas capas de Trotter tendrá el circuito del último paso?",
                ["10", "6", "4", "2"],
                "Anotado. En el siguiente paso lo comprobamos y vemos cómo se despliega.",
            ),
        ),
        beat(
            "desplegar",
            ("", "Desplegar una plantilla"),
            """Para desplegar una plantilla, descargas su carpeta source files del repositorio, y la subes con QiskitFunction, como en la primera lección de esta parte, declarando sus dependencias de pip.
             [[run]]La de AQC más Trotter solo exige tres entradas: el Hamiltoniano, una cadena unidimensional con vecinos cercanos, el número de pasos de Trotter y el plan de compresión. Esta es la respuesta a tu apuesta: seis. Dos capas del ansatz, más los cuatro pasos que no se comprimen.
             [[backends]]Y se puede ejecutar en tres sitios con el mismo código: statevector, exacto; fake, simulación ruidosa; y runtime, en un QPU real. Prueba primero en los simuladores: no gastan tiempo de QPU.""",
            [
                Code(
                    '''fn = QiskitFunction(title="aqc-dynamics-function", entrypoint="program.py",
                    working_dir="source_files/", dependencies=DEPENDENCIES)
serverless.upload(fn)
job = fn.run(hamiltonian=H, t_steps=10,
             aqc_segments=[{"n_steps": 6, "ansatz_steps": 2}],
             backend="statevector")      # o "fake", o "runtime"''',
                    id="c",
                    norun=True,
                    size=21,
                ),
                Table(
                    ["`backend`", "Qué es", "QPU"],
                    [
                        ["`statevector`", "exacto", "no"],
                        ["`fake`", "simulación con ruido", "no"],
                        ["`runtime`", "QPU real, con mitigación", "sí"],
                    ],
                    id="t",
                    hidden=True,
                    size=23,
                ),
            ],
            [
                A("hl", "c", at="desplegar", range="1-3"),
                A("hl", "c", at="run", range="4-5"),
                A("show", "t", at="backends"),
                A("hl", "c", at="backends", lines=[6]),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Buenas prácticas.""",
            [
                T(
                    "Tu función tarda 20 minutos en mapear el problema y después falla porque faltaba un argumento.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué buena práctica de las plantillas habría evitado esa pérdida?",
                [
                    "imprimir más registros",
                    "validar todas las entradas al principio del programa",
                    "usar más núcleos",
                ],
                1,
                "Correcto: leer y validar las entradas al principio hace que la función falle en segundos, antes de gastar recursos.",
                wrong=[
                    "Los registros ayudan a diagnosticar, pero no evitan el gasto.",
                    None,
                    "Más núcleos solo harían fallar antes por casualidad.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Abre el cuaderno de práctica de esta lección. Las plantillas se despliegan en Serverless y piden una cuenta; el cuaderno trae una versión local con la misma estructura y los backends statevector y fake.
             [[n1]]Primero ejecutas la misma función en los dos backends y miras cómo el ruido separa las curvas. [[n2]]Después reordenas la función para que valide antes de la etapa cara. [[n3]]Y por último calculas cuántas capas de Trotter deja un plan de compresión, con validación temprana.""",
            [
                Mission(
                    "practica/p8-plantillas.py",
                    [
                        (
                            1,
                            "Ejecuta la función en `statevector` y en `fake` y compara las curvas.",
                        ),
                        (2, "Mueve la validación antes de la etapa cara."),
                        (
                            3,
                            "Escribe `pasos_en_qpu(t_steps, plan)` y lanza `ValueError` si el plan no cabe.",
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
            ("", "Proyecto Ising: hito VIII"),
            """Con esto llegamos al hito ocho del proyecto Ising. [[obp]]En esta parte conociste los addons, y OBP en particular: llevar las últimas capas del circuito al observable. [[aqc]]AQC-Tensor, la técnica de la plantilla que acabas de ver, persigue lo mismo desde otro lado: comprimir las primeras capas en un circuito más corto.
             [[hito]]El hito ocho recalcula tu cadena de espines, reduce su profundidad con OBP, y te hace pensar en un presupuesto: cuántos términos estás dispuesto a medir a cambio de un circuito más corto.""",
            [
                Row(
                    Box(
                        "def",
                        "OBP",
                        T("absorbe las últimas capas en el observable", "body"),
                        id="a",
                        hidden=True,
                    ),
                    Box(
                        "idea",
                        "AQC-Tensor",
                        T("comprime las primeras capas en un ansatz", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=24,
                ),
                Mission(
                    "practica/proyecto/hito8.py",
                    [
                        (
                            1,
                            "Recalcula el Hamiltoniano, la magnetización de Trotter y la profundidad transpilada.",
                        ),
                        (
                            2,
                            "Elige cuántas capas absorbe OBP: baja la profundidad un 25 % sin pasar de cien términos.",
                        ),
                        (
                            3,
                            "Escribe `ahorro(pasos)` con un presupuesto de operador y mira cómo cambia el ahorro con los pasos.",
                        ),
                    ],
                    title="Proyecto Ising · Hito VIII",
                    id="m",
                    hidden=True,
                ),
            ],
            [A("show", "a", at="obp"), A("show", "b", at="aqc"), A("show", "m", at="hito")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para pensar. Escribe con tus palabras; lo que escribas se guarda y lo verás al volver a esta lección.""",
            [T("Validar pronto y probar barato son la misma idea.", "subtitle")],
            ask=reflect(
                "¿Qué errores de tu función descubrirías con `statevector` antes de gastar tiempo de QPU, y cuáles solo con `fake`?",
                "En el hito ocho, con un límite fijo de términos, el ahorro de profundidad se queda constante al agregar pasos. ¿Qué implica eso para circuitos de Trotter muy largos, y cómo te ayudaría AQC-Tensor?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Plantillas de implementación de química y física. [[r2]]Plantillas base con buenas prácticas para tus funciones. [[r3]]Se despliegan en tu cuenta de Serverless.
             [[r4]]Valida pronto y prueba en simuladores antes del QPU. Con esto termina la Parte ocho.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "qiskit-function-templates",
        "function-template-chemistry-workflow",
        "function-template-hamiltonian-simulation",
        "function-template-aqc-trotter",
    ],
    practice=[
        "Clona el [repositorio de plantillas](https://github.com/qiskit-community/qiskit-function-templates) y lee la plantilla base de función de circuito.",
        "Sigue el tutorial de [dispersión de neutrones](https://quantum.cloud.ibm.com/docs/en/tutorials/simulate-neutron-scattering-with-a-serverless-workflow) que usa la plantilla AQC + Trotter.",
    ],
)

LESSONS = [serverless, addons, functions, circuit_functions, app_functions, plantillas]
