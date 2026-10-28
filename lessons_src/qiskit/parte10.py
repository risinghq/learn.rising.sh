"""Parte X · Organizaciones, seguridad y comunidad."""

from lib import (
    A,
    Box,
    Code,
    Flow,
    L,
    M,
    Mission,
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

# ------------------------------------------------------------------ 10.1 Organizaciones e instancias
s_cierre, a_cierre = resumen(
    [
        "instancia = despliegue del servicio con un plan y una región · se identifica por su CRN",
        "planes: Open (10 min / 28 días), Pay-As-You-Go, Flex, Premium",
        "asignación de tiempo → prioridad de reparto justo · límite opcional: nada se cancela",
        "configurar: IAM, grupos de recursos, instancias, grupos de acceso, IDP, firewall · API Resource Controller",
    ]
)
organizaciones = lesson(
    "p10-organizaciones",
    "Organizaciones e instancias",
    "Planificar IBM Quantum Platform para una organización: instancias, planes, regiones, asignaciones y límites, la API de gestión y los registros de plataforma.",
    [
        "entender qué es una instancia y qué decide su región y su plan",
        "planificar el acceso de una organización",
        "configurar asignaciones y límites de uso",
    ],
    [
        beat(
            "instancia",
            ("", "¿Qué es una instancia?"),
            """El acceso a IBM Quantum Platform se controla con instancias: despliegues del servicio de computación cuántica que gestionan tus trabajos, cuánticos y clásicos. Cada una se identifica por su CRN, el nombre de recurso de la nube.
             [[plan]]Cada instancia tiene un plan y una región: necesitas una instancia por cada plan y cada región que quieras usar. [[region]]La región, Washington, us east, o Frankfurt, eu de, decide qué QPUs ves, dónde se hace la compilación y dónde quedan tus datos: circuitos, parámetros y resultados.
             [[uso]]Todo lo que ejecutan los colaboradores de una instancia cuenta para su uso.""",
            [
                Table(
                    ["Una instancia tiene", ""],
                    [
                        ["un plan", "Open · Pay-As-You-Go · Flex · Premium"],
                        ["una región", "`us-east` · `eu-de`"],
                        ["un CRN", "`crn:v1:bluemix:public:quantum-computing:…`"],
                    ],
                    id="t",
                    stagger=True,
                    size=23,
                ),
                T(
                    "la región decide: QPUs disponibles · dónde se compila · dónde quedan los datos",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("item", "t", at="plan", i=0),
                A("item", "t", at="region", i=1),
                A("show", "n", at="region", t=3),
                A("item", "t", at="instancia", t=6, i=2),
            ],
        ),
        beat(
            "planes",
            ("", "Los planes"),
            """Hay cuatro planes. [[open]]Open es gratuito: hasta diez minutos de QPU en una ventana móvil de veintiocho días, y solo en la región us east. [[payg]]Pay As You Go cobra por uso, con un límite de costo opcional.
             [[flex]]Flex y Premium se contratan con IBM: tienen tiempo asignado, y el administrador puede limitar cada instancia; en Flex el límite vale durante el contrato, en Premium por ventana de veintiocho días.
             [[codigo]]En tu código, eliges la instancia por CRN o por nombre al crear el servicio; si no la indicas, ves backends y trabajos de todas, y desde la cero punto cuarenta y dos se priorizan los planes gratuitos al elegir una automáticamente.""",
            [
                Table(
                    ["Plan", "Costo", "Particularidad"],
                    [
                        ["Open", "gratis", "10 min / 28 días · solo `us-east`"],
                        ["Pay-As-You-Go", "por uso", "límite de costo opcional"],
                        ["Flex", "contrato", "límite durante el contrato"],
                        ["Premium", "contrato", "límite por ventana de 28 días"],
                    ],
                    id="t",
                    stagger=True,
                    size=23,
                ),
                Code(
                    """service = QiskitRuntimeService(instance="<CRN o nombre>")""",
                    id="c",
                    hidden=True,
                    norun=True,
                ),
            ],
            [
                A("item", "t", at="open", i=0),
                A("item", "t", at="payg", i=1),
                A("item", "t", at="flex", i=2),
                A("item", "t", at="flex", t=3, i=3),
                A("show", "c", at="codigo"),
            ],
        ),
        beat(
            "planificar",
            ("", "Planificar una organización"),
            """Para una organización, primero hay que decidir varias cosas. [[ident]]Cómo se definen las identidades: usuarios de IBM Cloud, de otro proveedor de identidad, o ambos. [[cuantas]]Cuántas instancias hacen falta y para qué: por ejemplo, una por equipo; los trabajos pertenecen a la instancia y todos sus usuarios los ven.
             [[quien]]Qué usuarios acceden a qué instancias, y si pueden borrar trabajos. [[grupos]]Y cómo organizar el acceso: con el grupo de colaboradores que se crea con cada instancia, con grupos propios, o con grupos de recursos, que separan instancias de forma rígida, porque una instancia no puede cambiar de grupo de recursos.""",
            [
                L(
                    [
                        "¿cómo se definen las identidades?",
                        "¿cuántas instancias y para qué?",
                        "¿quién accede a qué? ¿puede borrar trabajos?",
                        "¿grupos de acceso o grupos de recursos?",
                    ],
                    id="l",
                    stagger=True,
                )
            ],
            [
                A("item", "l", at="ident", i=0),
                A("item", "l", at="cuantas", i=1),
                A("item", "l", at="quien", i=2),
                A("item", "l", at="grupos", i=3),
            ],
        ),
        beat(
            "pasos",
            ("", "Los pasos de configuración"),
            """Los pasos, en orden. [[iam]]Uno: ajustar IAM, la visibilidad de la lista de usuarios y quién puede crear claves de API. [[rg]]Dos, opcional: crear grupos de recursos. [[inst]]Tres: crear las instancias, con nombres pensados, como QR ml.
             [[ag]]Cuatro: crear un rol personalizado y un grupo de acceso por instancia, con los permisos mínimos. [[idp]]Cinco: configurar el proveedor de identidad e invitar usuarios. [[fw]]Y seis: permitir en el cortafuegos los dominios de IBM Cloud y de la región.""",
            [
                Flow(
                    [
                        dict(t="IAM", s="visibilidad · claves de API"),
                        dict(t="grupos de recursos", s="opcional"),
                        dict(t="instancias"),
                        dict(t="roles y grupos de acceso", color="violet"),
                        dict(t="IDP y usuarios"),
                        dict(t="cortafuegos", s="`quantum.cloud.ibm.com` …", color="gold"),
                    ],
                    id="f",
                    stagger=True,
                    numbered=True,
                )
            ],
            [
                A("item", "f", at="iam", i=0),
                A("item", "f", at="rg", i=1),
                A("item", "f", at="inst", i=2),
                A("item", "f", at="ag", i=3),
                A("item", "f", at="idp", i=4),
                A("item", "f", at="fw", i=5),
            ],
        ),
        beat(
            "limite_pred",
            ("", "Antes de ver el límite"),
            """Antes de ver la regla, apuesta. Una instancia Premium tiene un límite de uso, y lo alcanza cuando tiene un trabajo en ejecución y tres en cola.
             [[cual]]¿Qué crees que pasa con esos cuatro trabajos? No hace falta acertar: apostar primero hace que la regla se te quede.""",
            [
                Table(
                    ["Instancia Premium con límite", ""],
                    [
                        ["trabajos en ejecución", "1"],
                        ["trabajos en cola", "3"],
                        ["uso", "alcanzó el límite"],
                    ],
                    id="t",
                    size=24,
                )
            ],
            ask=predict(
                "Al alcanzar el límite, ¿qué pasa con esos cuatro trabajos?",
                [
                    "los cuatro se cancelan",
                    "el que se ejecuta continúa y los tres en cola esperan a que haya tiempo",
                    "el que se ejecuta se detiene y los tres en cola pasan con menor prioridad",
                    "todos siguen como si nada",
                ],
                "Anotado. Veamos qué dice la regla.",
            ),
        ),
        beat(
            "asignacion",
            ("", "Asignaciones y límites"),
            """En Premium y Flex, la cuenta tiene un tiempo contratado que se reparte entre instancias. El tiempo asignado a cada una lo usa el planificador de reparto justo para su prioridad en la cola.
             [[limite]]La asignación puede ser además un límite. Cuando una instancia lo alcanza: lo que se está ejecutando sigue, lo pendiente queda en cola, y nada se cancela. Los colaboradores pueden enviar trabajos, pero esperan hasta que haya tiempo: en Flex, hasta que suban el límite; en Premium, hasta la siguiente ventana.
             [[sinlimite]]Si no es un límite y se supera la asignación, los trabajos siguen, pero con menor prioridad y colas más largas.""",
            [
                Table(
                    ["Al llegar al límite", ""],
                    [
                        ["trabajos en ejecución", "continúan"],
                        ["trabajos pendientes", "siguen en cola"],
                        ["cancelaciones", "ninguna"],
                        ["trabajos nuevos", "esperan a que haya tiempo"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                ),
                T(
                    "sin límite y por encima de la asignación → menor prioridad",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("item", "t", at="limite", i=0),
                A("item", "t", at="limite", t=3, i=1),
                A("item", "t", at="limite", t=5, i=2),
                A("item", "t", at="limite", t=7, i=3),
                A("show", "n", at="sinlimite"),
            ],
        ),
        beat(
            "api",
            ("", "Gestión por API y registros"),
            """Las instancias se pueden gestionar por programa con la API Resource Controller de IBM Cloud: obtener, listar, crear y actualizar instancias, autenticándote con un token bearer.
             [[ext]]Además de los campos estándar, la respuesta incluye campos cuánticos: el límite de uso en segundos, la asignación en segundos, y la lista de backends permitidos, donde ANY significa todos los del plan. La misma API sirve para habilitar Qiskit Functions en una instancia.
             [[logs]]Y para auditoría, el servicio genera registros de plataforma cada vez que cambia el estado de un trabajo, que IBM Cloud Logs Routing envía a donde configures.""",
            [
                Sh(
                    """curl --request GET \\
  --url 'https://resource-controller.cloud.ibm.com/v2/resource_instances/<CRN_codificado>' \\
  --header 'Authorization: Bearer <TOKEN>\'""",
                    id="c",
                ),
                Table(
                    ["Campo en `extensions`", "Significado"],
                    [
                        ["`instance_limit_seconds`", "límite de uso"],
                        ["`usage_allocation_seconds`", "asignación (reparto justo)"],
                        ["`backends`", 'backends permitidos (`["ANY"]` = todos)'],
                    ],
                    id="t",
                    hidden=True,
                    size=22,
                ),
            ],
            [A("show", "t", at="ext"), A("hl", "c", at="logs", lines=[2], dim=False)],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Ahora el caso contrario: una asignación que no es un límite.""",
            [
                T(
                    "Una instancia Flex superó su tiempo asignado, pero la asignación no estaba marcada como límite.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué pasa con sus trabajos nuevos?",
                [
                    "se cancelan",
                    "esperan hasta que suban el límite",
                    "siguen, con menor prioridad y colas más largas",
                ],
                2,
                "Correcto: sin límite no se bloquea nada; la instancia pierde prioridad en el reparto justo y sus colas se alargan.",
                wrong=[
                    "Nunca se cancelan trabajos por superar la asignación.",
                    "Eso pasa cuando la asignación sí es un límite.",
                    None,
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. Abre el cuaderno de práctica de esta lección con el comando de abajo. [[n1]]Primero lees una instancia con la API de gestión: el CRN va codificado en la ruta, y la respuesta trae los campos cuánticos. [[n2]]Después arreglas el cálculo de cuánto te queda en el plan Open: la ventana de veintiocho días se mueve, y los usos viejos dejan de contar.
             [[n3]]Y por último escribes qué pasa con los trabajos al llegar a un límite, con y sin límite, sin cancelar ninguno. Las comprobaciones se actualizan solas: busca la marca verde.""",
            [
                Mission(
                    "practica/p10-organizaciones.py",
                    [
                        (1, "Codifica el CRN de una instancia y lee los campos de `extensions`."),
                        (
                            2,
                            "Corrige `restante` para que solo cuente la ventana móvil de 28 días del plan Open.",
                        ),
                        (3, "Escribe `tras_alcanzar`: qué pasa con cada trabajo con y sin límite."),
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
            """Dos preguntas para pensar con calma. Escribe con tus palabras: lo que escribas se guarda en tu navegador.""",
            [
                T(
                    "Un límite protege el presupuesto; una asignación solo reparte prioridad.",
                    "subtitle",
                )
            ],
            ask=reflect(
                "¿Por qué crees que alcanzar un límite deja los trabajos en cola en lugar de cancelarlos? ¿Qué se perdería si se cancelaran?",
                "Tu laboratorio tiene dos equipos y un proyecto compartido. ¿Cuántas instancias crearías, y cuáles tendrían un límite y cuáles solo una asignación?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Una instancia tiene un plan, una región y un CRN. [[r2]]Hay cuatro planes, de Open a Premium. [[r3]]Las asignaciones dan prioridad, y los límites detienen el consumo sin cancelar nada.
             [[r4]]Y la configuración se planifica: identidades, instancias, grupos y cortafuegos.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "considerations-set-up-runtime",
        "quickstart-steps-org",
        "instances",
        "allocation-limits",
        "access-instances-platform-apis",
        "logging",
    ],
    practice=[
        "Diseña la estructura de instancias y grupos para un laboratorio con dos equipos y un proyecto compartido.",
        "Consulta con la API Resource Controller los campos `extensions` de una de tus instancias.",
    ],
)

# ------------------------------------------------------------------ 10.2 Acceso
s_cierre, a_cierre = resumen(
    [
        "cuenta de IBM Cloud: usuarios, instancias, políticas de acceso, grupos de acceso",
        "roles de plataforma (Viewer, Operator, Editor, Administrator) y de servicio (Reader, Writer, Manager)",
        "ejecutar trabajos: Writer de servicio + Viewer de plataforma · roles personalizados para afinar",
        "usuarios: invitar desde Access management o IAM · IDP externo con SAML o App ID y reglas dinámicas",
    ]
)
acceso = lesson(
    "p10-acceso",
    "Cuentas, grupos de acceso y usuarios",
    "La estructura de una cuenta de IBM Cloud, los roles de plataforma y de servicio, los grupos de acceso, los roles personalizados y la gestión de usuarios.",
    [
        "entender la estructura de cuentas, políticas y grupos de IBM Cloud",
        "elegir los roles mínimos para cada tarea",
        "invitar y gestionar usuarios",
    ],
    [
        beat(
            "estructura",
            ("", "La estructura de una cuenta"),
            """Una cuenta de IBM Cloud contiene usuarios e instancias de servicio. [[politicas]]A cada usuario se le asignan políticas de acceso, que dan permisos sobre instancias, [[grupos]]y las políticas se agrupan en grupos de acceso, que es la forma habitual de gestionarlas.
             [[visible]]Por defecto, todos los usuarios de una cuenta se ven entre sí; se puede restringir.""",
            [
                Flow(
                    [
                        dict(t="cuenta"),
                        dict(t="usuarios"),
                        dict(t="grupos de acceso", s="políticas", color="violet"),
                        dict(t="instancias", color="teal"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="estructura", i=0),
                A("item", "f", at="estructura", t=3, i=1),
                A("item", "f", at="politicas", i=2),
                A("item", "f", at="politicas", t=3, i=3),
            ],
        ),
        beat(
            "roles",
            ("", "Dos familias de roles"),
            """Los roles son de dos familias. [[plataforma]]Los de plataforma gestionan recursos: Viewer ve instancias; Operator además gestiona credenciales; Editor crea, edita y borra instancias; y Administrator puede hacer todo, incluido asignar acceso.
             [[servicio]]Los de servicio actúan dentro de la instancia: Reader solo lee, por ejemplo ve trabajos; Writer además ejecuta trabajos; y Manager además crea instancias, fija límites de costo y borra o cancela trabajos de otros.
             [[combinar]]Muchas acciones combinan ambos: para ejecutar trabajos hace falta Writer de servicio y Viewer de plataforma sobre la instancia.""",
            [
                Row(
                    Table(
                        ["Plataforma", ""],
                        [
                            ["Viewer", "ver instancias"],
                            ["Operator", "+ credenciales"],
                            ["Editor", "+ crear y borrar instancias"],
                            ["Administrator", "todo"],
                        ],
                        id="p",
                        stagger=True,
                        size=21,
                    ),
                    Table(
                        ["Servicio", ""],
                        [
                            ["Reader", "solo lectura"],
                            ["Writer", "+ ejecutar trabajos"],
                            ["Manager", "+ instancias, límites, cancelar"],
                        ],
                        id="s",
                        stagger=True,
                        size=21,
                    ),
                    gap=20,
                ),
                T(
                    "ejecutar trabajos = Writer (servicio) + Viewer (plataforma)",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("item", "p", at="plataforma", i=0),
                A("item", "p", at="plataforma", t=2, i=1),
                A("item", "p", at="plataforma", t=4, i=2),
                A("item", "p", at="plataforma", t=6, i=3),
                A("item", "s", at="servicio", i=0),
                A("item", "s", at="servicio", t=3, i=1),
                A("item", "s", at="servicio", t=5, i=2),
                A("show", "n", at="combinar"),
            ],
        ),
        beat(
            "grupos",
            ("", "Grupos de acceso"),
            """Cada instancia creada desde la plataforma trae su grupo de colaboradores. Para la administración, se recomienda crear además un grupo de administradores de IBM Quantum.
             [[politicas]]Sus políticas: Manager y Administrator sobre el servicio cuántico; Viewer sobre la gestión de la cuenta, para listar grupos de recursos; Administrator sobre la gestión de IAM, para invitar usuarios y gestionar accesos; y Administrator del centro de soporte, para abrir casos.
             [[cli]]Los grupos se crean desde la consola, la CLI o la API de IBM Cloud.""",
            [
                Table(
                    ["Política", "Roles"],
                    [
                        ["IBM Quantum Compute Service", "Manager + Administrator"],
                        ["All account management services", "Viewer"],
                        ["All IAM Account Management services", "Administrator"],
                        ["Support Center", "Administrator"],
                    ],
                    id="t",
                    stagger=True,
                    size=22,
                ),
                Sh(
                    '''ibmcloud iam access-group-create GROUP_NAME -d "Administradores de IBM Quantum"''',
                    id="c",
                    hidden=True,
                ),
            ],
            [
                A("item", "t", at="politicas", i=0),
                A("item", "t", at="politicas", t=4, i=1),
                A("item", "t", at="politicas", t=7, i=2),
                A("item", "t", at="politicas", t=10, i=3),
                A("show", "c", at="cli"),
            ],
        ),
        beat(
            "custom_pred",
            ("", "Antes de los roles personalizados"),
            """Antes de verlos, apuesta. Un rol personalizado se compone de acciones concretas del servicio. Este tiene siete: leer dispositivos, crear, leer y cancelar trabajos, leer y borrar programas, y cerrar sesión.
             [[cual]]Un usuario con este rol, ¿podrá borrar un trabajo?""",
            [
                Code(
                    """quantum-computing.device.read
quantum-computing.job.create
quantum-computing.job.read
quantum-computing.job.cancel
quantum-computing.program.read
quantum-computing.program.delete
quantum-computing.user.logout""",
                    "text",
                    id="c",
                    size=22,
                )
            ],
            ask=predict(
                "¿Puede este usuario borrar un trabajo (`DELETE /v1/jobs/{id}`)?",
                [
                    "sí: puede crearlos y cancelarlos, así que también borrarlos",
                    "no: borrar trabajos es una acción aparte que no está en la lista",
                    "sí, porque puede borrar programas",
                    "solo si además es administrador de la cuenta",
                ],
                "Anotado. Veamos la lista completa.",
            ),
        ),
        beat(
            "custom",
            ("", "Roles personalizados"),
            """Cuando los roles predefinidos no encajan, se crean roles personalizados eligiendo acciones concretas del servicio. [[trabajo]]Por ejemplo, un rol para trabajar con instancias: leer dispositivos, crear, leer y cancelar trabajos, leer y borrar programas, cerrar sesión, y opcionalmente borrar trabajos. Borrar programas no es borrar trabajos: son acciones distintas.
             [[analitica]]O un rol que solo ve la analítica de uso. [[lector]]Un patrón útil: dos roles, uno lector sin acciones de cancelar, borrar ni actualizar, y otro escritor con todas, cada uno en su grupo.""",
            [
                Code(
                    """quantum-computing.device.read
quantum-computing.job.create
quantum-computing.job.read
quantum-computing.job.cancel
quantum-computing.program.read
quantum-computing.program.delete
quantum-computing.user.logout
quantum-computing.job.delete        # opcional""",
                    "text",
                    id="c",
                    size=22,
                ),
                Row(
                    Box("def", "MLreader", T("sin cancelar, borrar ni actualizar", "body")),
                    Box("def", "MLwriter", T("todas las acciones", "body")),
                    id="r",
                    hidden=True,
                    gap=24,
                ),
            ],
            [A("hl", "c", at="trabajo", range="1-7"), A("show", "r", at="lector")],
        ),
        beat(
            "usuarios",
            ("", "Invitar y gestionar usuarios"),
            """Crea las instancias antes de invitar. Desde Access management, en la plataforma, invitas por correo y asignas grupos; el usuario recibe la invitación y verá la nueva cuenta en su selector. [[cloud]]Si ya tiene cuenta de IBM Cloud, también se le invita desde IAM; no se le puede gestionar hasta que acepte y entre una vez.
             [[quitar]]Al quitar a alguien de una instancia, deja de ver sus trabajos, pero los demás siguen viéndolos. [[idp]]Para inicio de sesión único, se conecta un proveedor de identidad externo, por SAML o con App ID, y con reglas dinámicas los usuarios se asignan solos a grupos.
             [[subcadenas]]Un cuidado: en las reglas dinámicas, no uses valores que sean subcadenas de otros, como ml y chemlab: la regla de ml también daría acceso a chemlab.""",
            [
                Flow(
                    [
                        dict(t="crear instancias"),
                        dict(t="invitar", s="Access management o IAM"),
                        dict(t="asignar grupos", color="violet"),
                        dict(t="usuario acepta", color="teal"),
                    ],
                    id="f",
                    stagger=True,
                ),
                T(
                    "reglas dinámicas: evita valores que sean subcadenas (`ml` ⊂ `chemlab`)",
                    "note",
                    id="n",
                    hidden=True,
                    color="red",
                ),
            ],
            [
                A("item", "f", at="usuarios", i=0),
                A("item", "f", at="usuarios", t=2, i=1),
                A("item", "f", at="usuarios", t=5, i=2),
                A("item", "f", at="cloud", i=3),
                A("show", "n", at="subcadenas"),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Roles mínimos.""",
            [
                T(
                    "Una estudiante debe poder ejecutar trabajos en una instancia, pero no crear instancias ni cancelar trabajos ajenos.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué roles le das sobre esa instancia?",
                [
                    "Manager (servicio) + Editor (plataforma)",
                    "Writer (servicio) + Viewer (plataforma)",
                    "Reader (servicio)",
                ],
                1,
                "Correcto: Writer permite ejecutar trabajos y Viewer de plataforma permite ver la instancia; sin permisos de gestión.",
                wrong=[
                    "Demasiados permisos: podría crear instancias y cancelar trabajos ajenos.",
                    None,
                    "Reader no permite ejecutar trabajos.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. Abre el cuaderno de práctica de esta lección con el comando de abajo. [[n1]]Primero compruebas qué llamadas de la API permite el rol de trabajar con instancias, y confirmas si puede borrar trabajos. [[n2]]Después derivas un rol lector a partir del escritor, quitando las acciones de cancelar, borrar y actualizar.
             [[n3]]Y por último escribes un detector de valores que son subcadenas de otros, para que una regla dinámica no dé más acceso del que pretendes. Busca la marca verde en cada misión.""",
            [
                Mission(
                    "practica/p10-acceso.py",
                    [
                        (1, "Lista qué llamadas de la API permite un rol personalizado."),
                        (2, "Deriva `lector` del escritor sin tocar las demás acciones."),
                        (
                            3,
                            "Escribe `conflictos(valores)` para detectar subcadenas como `ml` en `chemlab`.",
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
            """Dos preguntas para pensar con calma. Lo que escribas se guarda en tu navegador.""",
            [T("Dar menos permisos da más trabajo hoy y evita más problemas mañana.", "subtitle")],
            ask=reflect(
                "La guía recomienda dar a cada persona los permisos mínimos. ¿Qué riesgo concreto corre una organización que da Manager a todo el mundo?",
                "Tu equipo tiene estudiantes, investigadoras y una persona que audita el uso. ¿Qué grupos de acceso crearías y qué roles tendría cada uno?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Una cuenta tiene usuarios, instancias, políticas y grupos de acceso. [[r2]]Hay roles de plataforma y de servicio, y se combinan. [[r3]]Los roles personalizados afinan permisos.
             [[r4]]Y los usuarios se invitan desde la plataforma o IAM, o llegan desde un proveedor de identidad.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "cloud-account-structure",
        "access-groups",
        "custom-roles",
        "invite-and-manage-users",
        "manage-appid",
        "manage-cloud-users",
    ],
    practice=[
        "Revisa en [IAM Roles](https://cloud.ibm.com/iam/roles) las acciones de los roles Reader, Writer y Manager de Quantum Compute.",
        "Diseña un rol personalizado de solo lectura para auditores.",
    ],
)

# ------------------------------------------------------------------ 10.3 Seguridad
s_cierre, a_cierre = resumen(
    [
        "datos cifrados en reposo · borrar instancia o trabajo · retención 3 años",
        "responsabilidad compartida: IBM opera el servicio; tú gestionas accesos, claves y versiones",
        "red: VPE para tráfico privado · restricciones por contexto · alta disponibilidad en 3 zonas",
        "auditoría: Activity Tracker y permisos `quantum-computing.*` · Dependabot y políticas de seguridad",
    ]
)
seguridad = lesson(
    "p10-seguridad",
    "Seguridad y cumplimiento",
    "Protección y retención de datos, responsabilidades compartidas, conexiones privadas, restricciones por contexto, alta disponibilidad, auditoría y políticas de seguridad.",
    [
        "saber cómo se protegen y retienen tus datos",
        "distinguir tus responsabilidades de las de IBM",
        "conocer las herramientas de red, auditoría y disponibilidad",
    ],
    [
        beat(
            "datos",
            ("", "Tus datos"),
            """Los datos que guardas en IBM Cloud están cifrados en reposo con una clave aleatoria. [[borrar]]Borrar una instancia elimina todo su contenido: trabajos, resultados, parámetros y programas. Con el rol Manager también puedes borrar un trabajo concreto.
             [[retencion]]Mientras sigas usando el servicio, IBM conserva tus datos no borrados durante tres años.""",
            [
                L(
                    [
                        "cifrado en reposo",
                        "borrar instancia → borra todo su contenido",
                        "Manager: borrar trabajos individuales",
                        "retención: 3 años mientras uses el servicio",
                    ],
                    id="l",
                    stagger=True,
                )
            ],
            [
                A("item", "l", at="datos", i=0),
                A("item", "l", at="borrar", i=1),
                A("item", "l", at="borrar", t=5, i=2),
                A("item", "l", at="retencion", i=3),
            ],
        ),
        beat(
            "responsabilidades",
            ("", "Responsabilidad compartida"),
            """La seguridad es compartida. [[ibm]]IBM opera la infraestructura, entrega actualizaciones, notifica mantenimientos e incidentes, cumple los acuerdos de nivel de servicio y versiona las API.
             [[tu]]Tú gestionas el acceso con IAM, proteges tus claves de API, configuras la auditoría, sigues las notificaciones, y migras a versiones soportadas antes de que termine el soporte de la anterior.""",
            [
                Row(
                    Table(
                        ["IBM"],
                        [
                            ["infraestructura y actualizaciones"],
                            ["notificar incidentes"],
                            ["SLA de alta disponibilidad"],
                            ["versionar las API"],
                        ],
                        id="a",
                        stagger=True,
                        size=21,
                    ),
                    Table(
                        ["Tú"],
                        [
                            ["acceso con IAM"],
                            ["proteger tus claves"],
                            ["configurar auditoría"],
                            ["migrar de versión a tiempo"],
                        ],
                        id="b",
                        stagger=True,
                        size=21,
                    ),
                    gap=24,
                )
            ],
            [
                A("item", "a", at="ibm", i=0),
                A("item", "a", at="ibm", t=2, i=1),
                A("item", "a", at="ibm", t=4, i=2),
                A("item", "a", at="ibm", t=6, i=3),
                A("item", "b", at="tu", i=0),
                A("item", "b", at="tu", t=2, i=1),
                A("item", "b", at="tu", t=3, i=2),
                A("item", "b", at="tu", t=5, i=3),
            ],
        ),
        beat(
            "red_pred",
            ("", "Antes de la red privada"),
            """Antes de verlo, apuesta. Has creado un punto de acceso privado virtual, VPE, desde tu nube privada virtual. [[cual]]Ahora abres la consola web en el navegador, ejecutas un script con el SDK de Python y haces una llamada a la API REST. ¿Cuáles de las tres van por la red privada?""",
            [
                Flow(
                    [
                        dict(t="sitio web", s="navegador"),
                        dict(t="SDK de Python", s="qiskit-ibm-runtime"),
                        dict(t="API REST", s="curl"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="cual", i=0),
                A("item", "f", at="cual", t=2, i=1),
                A("item", "f", at="cual", t=4, i=2),
            ],
            ask=predict(
                "¿Cuáles de las tres conexiones van por el VPE?",
                [
                    "las tres",
                    "el SDK y la API, no el sitio web",
                    "solo la API REST",
                    "ninguna: el tráfico siempre sale a internet",
                ],
                "Anotado. Veamos qué dice la guía.",
            ),
        ),
        beat(
            "red",
            ("", "Conexiones privadas y restricciones"),
            """Dentro de la red de IBM, la comunicación siempre es privada. Pero tu conexión con la plataforma va por internet, salvo que uses un punto de acceso privado virtual, VPE, desde tu nube privada virtual: así el tráfico no sale a la red pública. Funciona con la API y el SDK, no con el sitio web.
             [[cbr]]Las restricciones basadas en contexto añaden una capa más: además de quién eres, comprueban desde dónde llega la petición, por ejemplo desde ciertas redes. No dan acceso; solo lo restringen.""",
            [
                Table(
                    ["Región", "Dominio privado (VPE)"],
                    [
                        ["`us-east`", "`private.us-east.quantum.cloud.ibm.com`"],
                        ["`eu-de`", "`private.eu-de.quantum.cloud.ibm.com`"],
                    ],
                    id="t",
                    size=22,
                ),
                Box(
                    "def",
                    "Restricciones por contexto",
                    T("comprueban desde dónde llega la petición · no conceden acceso", "body"),
                    id="b",
                    hidden=True,
                ),
            ],
            [A("show", "b", at="cbr")],
        ),
        beat(
            "ha",
            ("", "Alta disponibilidad"),
            """El servicio está desplegado en tres zonas de cada región, sin punto único de fallo: si una zona cae, las peticiones siguen por las otras sin degradación notable.
             [[dr]]Ante un desastre regional, IBM reconstruye el servicio. Lo recomendado para ti: crear una instancia en la otra región y reenviar los trabajos afectados, salvo que necesites qubits concretos de esa región o tengas requisitos de residencia de datos; en ese caso, esperar la recuperación.""",
            [
                Flow([dict(t="zona 1"), dict(t="zona 2"), dict(t="zona 3")], id="f", stagger=True),
                T(
                    "caída regional → instancia en la otra región (si los datos y los qubits lo permiten)",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("item", "f", at="ha", i=0),
                A("item", "f", at="ha", t=1, i=1),
                A("item", "f", at="ha", t=2, i=2),
                A("show", "n", at="dr"),
            ],
        ),
        beat(
            "auditoria",
            ("", "Auditoría y permisos"),
            """Para auditoría, el servicio genera eventos de actividad que IBM Cloud Activity Tracker Event Routing envía a donde configures, y que puedes ver y alertar con IBM Cloud Logs. [[acciones]]Cada evento corresponde a una acción, como crear o cancelar un trabajo; [[permisos]]y esas mismas acciones son los permisos que componen los roles: por ejemplo, job create para ejecutar un trabajo. Hay un catálogo equivalente para el acceso directo a sistemas.""",
            [
                Table(
                    ["Permiso", "Lo requiere"],
                    [
                        ["`quantum-computing.job.create`", "`POST /v1/jobs`"],
                        ["`quantum-computing.job.cancel`", "`POST /v1/jobs/{id}/cancel`"],
                        ["`quantum-computing.device.read`", "`GET /v1/backends`"],
                        ["`quantum-computing.instance-usage.read`", "`GET /v1/instances/usage`"],
                    ],
                    id="t",
                    stagger=True,
                    size=21,
                )
            ],
            [
                A("item", "t", at="acciones", i=0),
                A("item", "t", at="acciones", t=2, i=1),
                A("item", "t", at="permisos", i=2),
                A("item", "t", at="permisos", t=3, i=3),
            ],
        ),
        beat(
            "politicas",
            ("", "Políticas de seguridad del código"),
            """Y en tu propio entorno: mantén tus dependencias al día con herramientas como Dependabot, que te avisan cuando hay versiones vulnerables. Cada repositorio de Qiskit, el SDK, el cliente y los addons, publica su política de seguridad, con cómo reportar vulnerabilidades.""",
            [
                Box(
                    "idea",
                    "Buena práctica",
                    T(
                        "Dependabot u otra herramienta que avise de dependencias desactualizadas",
                        "body",
                    ),
                ),
                T("cada repositorio de Qiskit publica su `SECURITY.md`", "note"),
            ],
            [],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Sobre responsabilidades.""",
            [T("Una clave de API de tu equipo apareció en un repositorio público.", "body")],
            ask=choice(
                "¿De quién es la responsabilidad de actuar y qué haces?",
                [
                    "de IBM: detectará el uso indebido",
                    "tuya: revocar la clave de inmediato y crear otra",
                    "de nadie: las claves no caducan",
                ],
                1,
                "Correcto: proteger las claves es tu responsabilidad; revócala borrándola en IBM Cloud API keys y crea una nueva.",
                wrong=[
                    "Proteger las claves es responsabilidad del cliente.",
                    None,
                    "Justamente por eso hay que revocarla.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. Abre el cuaderno de práctica de esta lección con el comando de abajo. [[n1]]Primero lees una auditoría: conviertes eventos de actividad en los permisos que se ejercieron. [[n2]]Después amplías un detector de claves de API escritas en el código, sin marcar las que vienen del entorno.
             [[n3]]Y por último escribes qué hacer ante una caída regional, según tu plan, tus qubits y la residencia de tus datos. Todo con datos de ejemplo, sin cuenta. Busca la marca verde.""",
            [
                Mission(
                    "practica/p10-seguridad.py",
                    [
                        (1, "Cuenta qué permisos ejercen los eventos de una auditoría."),
                        (2, "Amplía el patrón que detecta claves de API en el código."),
                        (
                            3,
                            "Escribe `ante_desastre`: esperar o crear una instancia en la otra región.",
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
            """Dos preguntas para pensar con calma. Lo que escribas se guarda en tu navegador.""",
            [
                T(
                    "La seguridad es compartida: saber qué te toca a ti es la mitad del trabajo.",
                    "subtitle",
                )
            ],
            ask=reflect(
                "Una clave de API de tu equipo apareció en un repositorio público. Describe con tus palabras qué haces en los primeros diez minutos y por qué.",
                "En tu proyecto Ising, ¿qué parte dependería de qubits concretos de una región y cuál podrías reenviar sin cambios a otra?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Tus datos están cifrados y se retienen tres años. [[r2]]La seguridad es compartida entre IBM y tú. [[r3]]Hay conexiones privadas, restricciones por contexto y alta disponibilidad en tres zonas.
             [[r4]]Y la auditoría registra cada acción.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "secure-data",
        "responsibilities",
        "virtual-private-endpoints",
        "ha-dr",
        "observability-runtime-rest",
        "observability-quantum-system",
        "authorization-roles",
        "security-policies",
        "context-based-restrictions",
    ],
    practice=[
        "Activa Dependabot en un repositorio tuyo que use Qiskit.",
        "Revisa en la guía de [responsabilidades](https://quantum.cloud.ibm.com/docs/en/guides/responsibilities) qué te toca en recuperación ante desastres.",
    ],
)

# ------------------------------------------------------------------ 10.4 Comunidad
s_cierre, a_cierre = resumen(
    [
        "soporte: IBM Cloud Support Center (casos) · comunidad: Slack de Qiskit, Stack Exchange",
        "errores y propuestas: issues en GitHub de cada repositorio",
        "citar Qiskit (BibTeX) y los QPUs por nombre y versión",
        "código abierto desde 2016 · código de conducta: respeto, inclusión, colaboración",
    ]
)
comunidad = lesson(
    "p10-comunidad",
    "Soporte, preguntas frecuentes y código abierto",
    "Dónde pedir ayuda, las preguntas frecuentes, cómo citar Qiskit y los QPUs, y cómo participar en la comunidad de código abierto.",
    [
        "saber dónde pedir ayuda según tu plan",
        "citar Qiskit y los QPUs de IBM",
        "participar en la comunidad respetando su código de conducta",
    ],
    [
        beat(
            "soporte",
            ("", "Pedir ayuda"),
            """Con cualquier plan, salvo las cuentas de prueba, las consultas van al centro de soporte de IBM Cloud, abriendo un caso sobre Quantum Compute: errores de trabajos, problemas de la plataforma, dudas de Qiskit o de computación cuántica.
             [[comunidad]]Para ayuda de la comunidad: el Slack de Qiskit, con canales temáticos, y Stack Exchange de computación cuántica. [[github]]Y para reportar errores o pedir funciones, los issues de GitHub de cada repositorio: el SDK, el cliente, Serverless o el transpilador con IA.""",
            [
                Table(
                    ["Necesidad", "Dónde"],
                    [
                        ["soporte técnico (planes)", "IBM Cloud Support Center"],
                        ["ayuda de la comunidad", "Slack de Qiskit · Stack Exchange"],
                        ["errores y propuestas", "issues en GitHub"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                )
            ],
            [
                A("item", "t", at="soporte", i=0),
                A("item", "t", at="comunidad", i=1),
                A("item", "t", at="github", i=2),
            ],
        ),
        beat(
            "cuenta",
            ("", "Problemas de cuenta"),
            """Si no puedes crear una cuenta, abre un caso de verificación de cuenta. Si tu país no admite cuentas personales, puedes usar la documentación y los cursos sin cuenta, una cuenta académica de SkillsBuild si eres estudiante o docente, o una cuenta de prueba de treinta días.
             [[inactiva]]Si ves que tu cuenta está inactiva, revisa en IBM Cloud si tienes pasos pendientes. [[invitado]]Y si te invitaron a una cuenta, basta aceptar la invitación, sin dar datos de facturación.""",
            [
                L(
                    [
                        "documentación y cursos sin cuenta",
                        "SkillsBuild (estudiantes y docentes)",
                        "cuenta de prueba: 30 días",
                    ],
                    id="l",
                    stagger=True,
                )
            ],
            [
                A("item", "l", at="cuenta", t=6, i=0),
                A("item", "l", at="cuenta", t=8, i=1),
                A("item", "l", at="cuenta", t=10, i=2),
            ],
        ),
        beat(
            "faq",
            ("", "Preguntas frecuentes"),
            """Algunas preguntas frecuentes. [[tarjeta]]¿Uso el plan Open y puse mi tarjeta: me cobrarán? No, salvo que crees una instancia Pay As You Go y la uses. [[clave]]¿Clave de API o token de API? Son lo mismo. Un token bearer, en cambio, es temporal.
             [[region]]¿Tengo que elegir mi región? No: la región decide dónde se ejecuta y dónde se guardan los datos; el plan Open solo está en us east. [[proxy]]¿Puedo usar un proxy? Sí, desde la versión cero punto cuarenta y cuatro del cliente. [[aer]]¿Y dónde quedó Aer? Desde Qiskit uno punto cero, pip install qiskit solo instala el SDK: Aer y los demás se instalan aparte.""",
            [
                Table(
                    ["Pregunta", "Respuesta"],
                    [
                        [
                            "¿Open con tarjeta: me cobran?",
                            "no, salvo con una instancia Pay-As-You-Go",
                        ],
                        ["¿clave de API vs token de API?", "lo mismo (bearer: temporal)"],
                        ["¿debo usar mi región?", "no · Open solo en `us-east`"],
                        ["¿proxy?", "sí, cliente ≥ 0.44"],
                        ["¿Aer?", "`pip install qiskit-aer` aparte"],
                    ],
                    id="t",
                    stagger=True,
                    size=22,
                )
            ],
            [
                A("item", "t", at="tarjeta", i=0),
                A("item", "t", at="clave", i=1),
                A("item", "t", at="region", i=2),
                A("item", "t", at="proxy", i=3),
                A("item", "t", at="aer", i=4),
            ],
        ),
        beat(
            "citar_pred",
            ("", "Antes de citar"),
            """Antes de verlo, apuesta. Escribes un artículo y ejecutaste tu experimento en el QPU ibm fez. [[cual]]¿Qué datos del QPU debe llevar la cita?""",
            [
                Flow(
                    [dict(t="tu artículo"), dict(t="ibm_fez", s="el QPU que usaste", color="teal")],
                    id="f",
                    stagger=True,
                )
            ],
            [A("item", "f", at="cual", i=0), A("item", "f", at="cual", t=2, i=1)],
            ask=predict(
                "¿Qué debe llevar la cita del QPU?",
                [
                    "solo «IBM Quantum», sin más datos",
                    "su nombre único, y opcionalmente su versión; conviene nombrar el procesador",
                    "el nombre de la persona que lo opera",
                    "la dirección IP del sistema",
                ],
                "Anotado. Veamos qué recomienda la guía.",
            ),
        ),
        beat(
            "citar",
            ("", "Citar en tu investigación"),
            """Si usas Qiskit en un artículo, cítalo con el archivo BibTeX del repositorio. [[agradecer]]Para los equipos de IBM, se recomienda un agradecimiento, y citar IBM Quantum con su dirección y el año. [[qpu]]Los QPUs se citan por su nombre único, opcionalmente con la versión, y conviene mencionar el tipo de procesador.""",
            [
                Box(
                    "def",
                    "Agradecimiento sugerido",
                    T(
                        "We acknowledge the use of IBM Quantum services for this work. The views expressed are those of the authors, and do not reflect the official policy or position of IBM or the IBM Quantum team.",
                        "body",
                    ),
                    id="b",
                    hidden=True,
                ),
                T(
                    "QPU: «In this paper we used `ibm_fez` (v1.2.8), an IBM Quantum Heron processor.»",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [A("show", "b", at="agradecer"), A("show", "n", at="qpu")],
        ),
        beat(
            "open",
            ("", "Código abierto"),
            """Desde dos mil dieciséis, IBM Quantum abrió el acceso a computadores cuánticos en la nube y liberó como código abierto partes clave de su software, empezando por Qiskit, hoy el entorno de computación cuántica más usado.
             [[contribuir]]Puedes contribuir de muchas formas: código mediante pull requests, documentación, o ayudando a otros en Slack. Para aportar código se firma un acuerdo de licencia de contribuidor.""",
            [
                Flow(
                    [
                        dict(t="2016", s="acceso en la nube"),
                        dict(t="Qiskit", s="código abierto"),
                        dict(t="ecosistema", s="proyectos de la comunidad", color="teal"),
                    ],
                    id="f",
                    stagger=True,
                ),
                L(["pull requests", "documentación", "ayuda en Slack"], id="l", hidden=True),
            ],
            [
                A("item", "f", at="open", i=0),
                A("item", "f", at="open", t=4, i=1),
                A("item", "f", at="open", t=8, i=2),
                A("show", "l", at="contribuir"),
            ],
        ),
        beat(
            "conducta",
            ("", "Código de conducta"),
            """La comunidad de Qiskit tiene un código de conducta: tratar a todos con respeto y dignidad, sin acoso, sin importar edad, apariencia, discapacidad, etnia, identidad de género, nivel de experiencia, nacionalidad, religión u orientación. Vale en línea y en persona.
             [[bien]]Se espera lenguaje acogedor e inclusivo, respeto por otros puntos de vista, aceptar la crítica constructiva, empatía, y colaborar antes que confrontar. [[mal]]No se acepta lenguaje o imágenes sexualizadas, insultos, acoso, ni publicar información privada de otros, aunque se diga en broma.""",
            [
                Row(
                    Box(
                        "idea",
                        "Sí",
                        T(
                            "lenguaje inclusivo · respeto · empatía · colaborar antes que confrontar",
                            "body",
                        ),
                        id="a",
                        hidden=True,
                    ),
                    Box(
                        "warn",
                        "No",
                        T(
                            "acoso · insultos · información privada ajena · aunque sea «en broma»",
                            "body",
                        ),
                        id="b",
                        hidden=True,
                    ),
                    gap=24,
                )
            ],
            [A("show", "a", at="bien"), A("show", "b", at="mal")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """¿Dónde pides ayuda?""",
            [T("Encontraste un error reproducible en el transpilador del SDK de Qiskit.", "body")],
            ask=choice(
                "¿Dónde lo reportas?",
                [
                    "en un caso de IBM Cloud Support",
                    "como issue en el GitHub de Qiskit",
                    "en un mensaje privado a un desarrollador",
                ],
                1,
                "Correcto: los errores del SDK se reportan como issues en github.com/Qiskit/qiskit, donde también se siguen las próximas versiones.",
                wrong=[
                    "El soporte de IBM es para tu cuenta y tus trabajos; los errores del SDK van a GitHub.",
                    None,
                    "Mejor en público, donde otros pueden reproducirlo y ayudar.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca. Abre el cuaderno de práctica de esta lección con el comando de abajo. [[n1]]Primero escribes la cita de un programa de IBM Quantum con la versión que tienes instalada. [[n2]]Después haces que la cita de un QPU sirva para cualquier backend, con su nombre, su versión y su familia.
             [[n3]]Y por último armas la sección de citas de un artículo: el agradecimiento, una frase por QPU y la referencia con el año. Usas backends simulados, sin cuenta. Busca la marca verde.""",
            [
                Mission(
                    "practica/p10-comunidad.py",
                    [
                        (1, "Cita un programa de IBM Quantum con la versión instalada."),
                        (
                            2,
                            "Haz que `cita_qpu` use el nombre, la versión y la familia del backend.",
                        ),
                        (
                            3,
                            "Escribe `seccion_de_citas(backends, anio)` con agradecimiento, QPU y referencia.",
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
            ("", "Tu proyecto: el informe final"),
            """Y el proyecto llega a su final. [[recalcula]]El hito diez es un informe reproducible. Recalculas la magnetización de tu cadena de espines: la curva exacta, los pasos de Trotter y la simulación con el ruido de Fake Fez.
             [[pasos]]Eliges cuántos pasos usar, equilibrando el error con la profundidad del circuito transpilado. [[informe]]Y escribes el informe: parámetros, tabla de resultados, versiones de software, y la cita de Qiskit y del QPU. Con las mismas semillas, cualquiera obtiene los mismos números.""",
            [
                M(r"M(t) = \frac{1}{N}\sum_i \langle Z_i \rangle", size=46),
                Mission(
                    "practica/proyecto/hito10.py",
                    [
                        (1, "Recalcula la curva exacta y compárala con 20 pasos de Trotter."),
                        (
                            2,
                            "Elige los pasos: error menor que 0.02 y profundidad transpilada de 200 o menos.",
                        ),
                        (
                            3,
                            "Escribe `informe(r, qpu, anio)` con parámetros, resultados, versiones y citas.",
                        ),
                    ],
                    title="Proyecto Ising · Hito X",
                    id="m",
                    hidden=True,
                    stagger=True,
                ),
            ],
            [
                A("show", "m", at="recalcula"),
                A("item", "m", at="recalcula", i=0),
                A("item", "m", at="pasos", i=1),
                A("item", "m", at="informe", i=2),
            ],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para cerrar el curso. Lo que escribas se guarda en tu navegador.""",
            [T("Un resultado que nadie puede reproducir es solo una anécdota.", "subtitle")],
            ask=reflect(
                "¿Qué necesita una persona ajena para reproducir tu informe dentro de un año? Haz una lista y marca qué parte ya incluye tu cuaderno.",
                "Alguien te pide ayuda en Slack con un error. ¿Qué datos pondrías al preguntar, o al abrir un issue, para que la comunidad pueda reproducirlo?",
            ),
        ),
        beat(
            "cierre",
            ("", "Fin del curso"),
            """Resumen. [[r1]]Soporte en IBM Cloud, comunidad en Slack y Stack Exchange. [[r2]]Errores y propuestas en GitHub. [[r3]]Cita Qiskit y los QPUs que uses.
             [[r4]]Y participa con respeto. Con esto terminas el recorrido completo por las guías de IBM Quantum y Qiskit. ¡Felicidades! Ahora, a practicar con hardware real.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["support", "faq", "open-source", "code-of-conduct"],
    practice=[
        "Únete al [Slack de Qiskit](https://qisk.it/join-slack) y busca el canal de tu tema favorito.",
        "Busca en GitHub un issue de Qiskit con la etiqueta «good first issue».",
    ],
)

LESSONS = [organizaciones, acceso, seguridad, comunidad]
