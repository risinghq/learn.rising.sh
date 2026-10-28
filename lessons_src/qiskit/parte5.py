"""Parte V · Ejecutar en IBM Quantum."""

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

# ------------------------------------------------------------------ 5.1 Cuenta y planes
s_cierre, a_cierre = resumen(
    [
        "cuenta de IBM Cloud → instancia (CRN) + clave API de 44 caracteres",
        "`save_account()` en equipos de confianza · en equipos públicos, clave a mano y luego borrarla",
        "selección automática de instancia: `plans_preference`, `region`, `tags`",
        "planes: Open (10 min/28 días), Pay-As-You-Go, Flex (≥400 min), Premium, On-Prem",
    ]
)
cuenta = lesson(
    "p5-cuenta",
    "Cuenta de IBM Cloud, planes y credenciales",
    "Crear la cuenta y una instancia, guardar y cargar credenciales de forma segura, elegir instancia, los planes de acceso y cómo limitar el gasto.",
    [
        "crear una instancia y obtener la clave API y el CRN",
        "guardar y cargar credenciales con `QiskitRuntimeService`",
        "comparar los planes y limitar el costo en Pay-As-You-Go",
    ],
    [
        beat(
            "piezas",
            ("", "Las piezas del acceso"),
            """Para ejecutar en los procesadores de IBM necesitas una cuenta de IBM Cloud. Dentro de ella creas instancias: cada instancia da acceso a los servicios cuánticos y se identifica con un CRN, un Cloud Resource Name.
             [[clave]]Además, tu cuenta tiene una clave API, también llamada token, de cuarenta y cuatro caracteres: es la que usa Qiskit para autenticarse.
             [[login]]Entras a IBM Quantum Platform con un IBMid o una cuenta de Google; esas credenciales no son las de la cuenta de IBM Cloud.
             [[region]]Y en la cabecera eliges cuenta y región: us east o eu de. La región decide dónde corren tus trabajos y dónde se guardan sus datos. Con la misma clave accedes a las dos, pero solo ves las instancias de la región en la que estás.""",
            [
                Flow(
                    [
                        dict(t="Cuenta IBM Cloud"),
                        dict(t="Instancia", s="identificada por su **CRN**"),
                        dict(t="Clave API", s="44 caracteres"),
                    ],
                    id="f",
                    stagger=True,
                ),
                Row(
                    Box(
                        "def", "Inicio de sesión", T("IBMid o Google", "body"), id="a", hidden=True
                    ),
                    Box(
                        "idea",
                        "Región",
                        T("`us-east` · `eu-de`: dónde corren y se guardan los trabajos", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=24,
                ),
            ],
            [
                A("item", "f", at="piezas", i=0),
                A("item", "f", at="piezas", t=3, i=1),
                A("item", "f", at="clave", i=2),
                A("show", "a", at="login"),
                A("show", "b", at="region"),
            ],
        ),
        beat(
            "guardar",
            ("", "Guardar las credenciales"),
            """En un equipo de confianza, como tu laptop, lo recomendable es guardar las credenciales una vez con save account.
             [[campos]]token es la clave API. instance, opcional, el CRN o el nombre de la instancia. name da un nombre a este juego de credenciales, set as default lo marca como predeterminado y overwrite permite reemplazarlo.
             [[auto]]Si no das instancia, puedes poner filtros para la selección automática: plans preference, region y tags.
             [[donde]]Se guardan en un archivo, qiskit ibm punto json, en la carpeta punto qiskit de tu usuario; no lo edites a mano.""",
            [
                Code(
                    """from qiskit_ibm_runtime import QiskitRuntimeService

QiskitRuntimeService.save_account(
    token="<TU_CLAVE_API>",          # 44 caracteres; nunca en código público
    instance="<CRN o nombre>",       # opcional
    name="mi-cuenta",                # opcional
    set_as_default=True,             # opcional
    overwrite=True,                  # opcional
)
# sin instancia, filtros para elegirla automáticamente:
#   plans_preference=["open"], region="us-east", tags=["…"]""",
                    id="c",
                    norun=True,
                    size=22,
                ),
                T(
                    "se guarda en `~/.qiskit/qiskit-ibm.json` · `service.saved_accounts()` lista lo guardado",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="campos", range="4-8"),
                A("hl", "c", at="auto", range="9-11"),
                A("show", "n", at="donde"),
            ],
        ),
        beat(
            "cargar",
            ("", "Cargar el servicio"),
            """Después, cada vez que lo necesites, basta con QiskitRuntimeService sin argumentos: carga las credenciales por defecto. [[nombre]]Con name eliges otro juego guardado.
             [[reglas]]Hay reglas sutiles. Si das token y name a la vez, se ignora el token y se usa la cuenta guardada. Si das name e instance, intenta esa instancia con esa cuenta. Y si guardaste varias sin marcar ninguna por defecto, se usa la que va última en orden alfabético.
             [[local]]Para pruebas locales existe channel igual a local, que no necesita credenciales.
             [[401]]Y un error frecuente: si recibes cuatrocientos uno, no autorizado, probablemente estás usando un token portador, de la API REST, en lugar de tu clave API.""",
            [
                Code(
                    """service = QiskitRuntimeService()                   # credenciales por defecto
service = QiskitRuntimeService(name="mi-cuenta")   # otro juego guardado
service = QiskitRuntimeService(token="<CLAVE>", instance="<CRN>")
service = QiskitRuntimeService(channel="local")    # pruebas locales
print(service.active_instance())""",
                    id="c",
                    norun=True,
                    size=22,
                ),
                Box(
                    "warn",
                    "401 Unauthorized",
                    T("¿usaste un token portador (bearer) en vez de tu clave API?", "body"),
                    id="b",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="cargar", lines=[1]),
                A("hl", "c", at="nombre", lines=[2]),
                A("hl", "c", at="local", lines=[4]),
                A("show", "b", at="401"),
            ],
        ),
        beat(
            "pred_instancia",
            ("", "Antes de elegir instancia"),
            """Imagina que tienes dos instancias con la misma clave y no das ninguna al crear el servicio. [[una]]La primera es del plan Open, gratuita. [[otra]]La segunda es de pago, Pay As You Go.
             [[cual]]Pides un procesador al que solo la instancia de pago tiene acceso. Apuesta: ¿qué instancia elegirá el servicio?""",
            [
                Table(
                    ["Instancia", "Plan", "¿Puede usar el procesador pedido?"],
                    [
                        ["instancia A", "Open · gratis", "no"],
                        ["instancia B", "Pay-As-You-Go", "sí"],
                    ],
                    id="t",
                    stagger=True,
                    size=26,
                )
            ],
            [A("item", "t", at="una", i=0), A("item", "t", at="otra", i=1)],
            ask=predict(
                "Pides ese procesador sin indicar instancia. ¿Cuál se usa?",
                [
                    "la A, porque es gratuita",
                    "la B, la única que puede usarlo",
                    "ninguna: da error",
                    "el servicio te pregunta cuál",
                ],
                "Anotado. Veamos el orden que sigue el servicio.",
            ),
        ),
        beat(
            "instancia",
            ("", "Selección automática de instancia"),
            """Si das la clave pero no la instancia, el servicio elige la más adecuada para lo que pides. [[orden]]El orden es este: si solo tienes acceso a una instancia, esa.
             [[guard]]Si las credenciales guardadas traen instancia, esa. [[varias]]Si varias instancias pueden usar el procesador pedido, decide tu preferencia de planes; por defecto, las gratuitas primero.
             [[una]]Y si solo una puede usarlo, se elige esa, aunque sea de pago: ojo, eso tiene costo. Esa es la respuesta de tu apuesta: la instancia B.
             [[cual]]La instancia elegida aparece en un aviso, y active instance te la muestra.""",
            [
                Flow(
                    [
                        dict(t="¿una sola instancia?"),
                        dict(t="¿instancia guardada?"),
                        dict(t="¿varias pueden?", s="preferencia de planes (gratis primero)"),
                        dict(t="¿solo una puede?", s="se usa, aunque cueste", color="red"),
                    ],
                    id="f",
                    stagger=True,
                    vertical=True,
                )
            ],
            [
                A("item", "f", at="orden", i=0),
                A("item", "f", at="guard", i=1),
                A("item", "f", at="varias", i=2),
                A("item", "f", at="una", i=3),
            ],
        ),
        beat(
            "seguridad",
            ("", "Equipos públicos"),
            """En un equipo que no es tuyo, una computadora pública por ejemplo, lo mejor es no ejecutar código. Si debes hacerlo, pasa la clave directamente al crear el servicio, sin guardarla, [[borrar]]y al terminar bórrala en la página de claves API y crea una nueva.
             [[nunca]]Regla de oro: nunca pongas tu clave en el código fuente, en un cuaderno o en un repositorio. Si se filtra, revócala de inmediato.""",
            [
                Code(
                    """service = QiskitRuntimeService(token="<CLAVE>", instance="<CRN>")   # sin save_account""",
                    id="c",
                    norun=True,
                ),
                Box(
                    "warn",
                    "Protege tu clave",
                    L(
                        [
                            "nunca en código, cuadernos ni Git",
                            "en equipos públicos: úsala y bórrala",
                            "si se filtra: revócala ya",
                        ],
                        size=26,
                    ),
                    id="b",
                    hidden=True,
                ),
            ],
            [A("show", "b", at="nunca")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Una pregunta sobre credenciales.""",
            [Code('service = QiskitRuntimeService(token="token_B", name="cuenta_A")', norun=True)],
            ask=choice(
                "¿Qué credenciales usa?",
                ["la clave `token_B`", "las guardadas como `cuenta_A`", "da error"],
                1,
                "Correcto: si das `name`, se cargan las credenciales guardadas con ese nombre y el `token` se ignora.",
                wrong=[
                    "Con `name` presente, el token se ignora.",
                    None,
                    "No da error; ignora el token.",
                ],
            ),
        ),
        beat(
            "planes",
            ("", "Los planes"),
            """IBM Quantum Platform tiene un plan gratuito y varios de pago. [[open]]El plan Open es gratis: hasta diez minutos de procesador cuántico por cada ventana móvil de veintiocho días, solo en la región us east. Desde marzo de dos mil veintiséis, los usuarios activos pueden sumar ciento ochenta minutos más durante un año.
             [[payg]]Pay As You Go: pagas solo lo que consumes. [[flex]]Flex: compras al menos cuatrocientos minutos por adelantado, para usar en un año, y los repartes entre instancias.
             [[prem]]Premium: una suscripción empresarial, con acceso, por ejemplo, a las Qiskit Functions. [[onprem]]Y On Prem: un sistema cuántico dedicado, instalado en tus instalaciones y mantenido por IBM.""",
            [
                Table(
                    ["Plan", "Qué ofrece"],
                    [
                        [
                            "Open",
                            "gratis · 10 min de QPU por 28 días · solo `us-east` · sin sesiones",
                        ],
                        ["Pay-As-You-Go", "pagas lo que consumes"],
                        ["Flex", "≥ 400 min prepagados, válidos un año"],
                        ["Premium", "suscripción empresarial · Qiskit Functions"],
                        ["On-Prem", "sistema dedicado en tus instalaciones"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                )
            ],
            [
                A("item", "t", at="open", i=0),
                A("item", "t", at="payg", i=1),
                A("item", "t", at="flex", i=2),
                A("item", "t", at="prem", i=3),
                A("item", "t", at="onprem", i=4),
            ],
        ),
        beat(
            "pred_limite",
            ("", "Antes de gastar"),
            """[[lim]]Supón que ya pagas por uso y fijaste un límite de costo en la instancia. [[corre]]Tienes un trabajo largo en ejecución. [[llega]]A mitad de camino, el gasto llega al límite. Apuesta: ¿qué pasa con ese trabajo?""",
            [
                Flow(
                    [
                        dict(t="límite de costo fijado"),
                        dict(t="trabajo largo en ejecución"),
                        dict(t="el gasto llega al límite", color="red"),
                    ],
                    id="f",
                    stagger=True,
                )
            ],
            [
                A("item", "f", at="lim", i=0),
                A("item", "f", at="corre", i=1),
                A("item", "f", at="llega", i=2),
            ],
            ask=predict(
                "¿Qué ocurre cuando se alcanza el límite?",
                [
                    "el trabajo termina y después no se envía ninguno más",
                    "los trabajos en curso se cancelan y no empieza ninguno más",
                    "el servicio sube el límite solo, para no perder el trabajo",
                    "nada: el límite es solo un aviso",
                ],
                "Anotado. Veamos qué hace el servicio.",
            ),
        ),
        beat(
            "costo",
            ("", "Controlar el gasto"),
            """Para pasar del plan Open a Pay As You Go, actualizas tu cuenta de IBM Cloud con una tarjeta y creas una instancia de ese plan. No se cobra nada hasta que envíes trabajos con ella.
             [[limite]]Lo primero que conviene hacer es fijar un límite de costo en la instancia: desde la página de instancias, la API o la línea de comandos de IBM Cloud. Se fija en dólares y se convierte a segundos de ejecución.
             [[alcanza]]Cuando se alcanza, los trabajos en curso se cancelan con el motivo ran too long, y no empieza ninguno más hasta subir el límite: esa es la respuesta correcta de tu apuesta. Ojo: el uso se reporta cada cierto tiempo, así que un trabajo puede pasarse un poco, y eso también se factura.
             [[aulas]]Para docentes existen las cuentas Classroom: plan Open para cada estudiante, sin tarjeta, gestionadas por el profesor.""",
            [
                Flow(
                    [
                        dict(t="cuenta con tarjeta"),
                        dict(t="instancia Pay-As-You-Go"),
                        dict(t="**límite de costo**", color="gold"),
                    ],
                    id="f",
                ),
                Box(
                    "warn",
                    "Al alcanzar el límite",
                    T(
                        "trabajos cancelados («Ran too long») · el uso puede pasarse un poco y se cobra",
                        "body",
                    ),
                    id="b",
                    hidden=True,
                ),
                T(
                    "Classroom: cuentas Open para estudiantes, sin tarjeta, con código de 32 dígitos",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("step", "f", at="limite", i=2),
                A("show", "b", at="alcanza"),
                A("show", "n", at="aulas"),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Una pregunta sobre planes.""",
            [T("Eres estudiante y quieres probar algoritmos en hardware real sin pagar.", "body")],
            ask=choice(
                "¿Qué plan y qué límite tienes?",
                [
                    "Open: 10 minutos por cada 28 días",
                    "Flex: 400 minutos al año",
                    "Premium: sin límite",
                ],
                0,
                "Correcto: el plan Open da hasta 10 minutos de QPU por ventana móvil de 28 días (y no permite sesiones).",
                wrong=[None, "Flex es de pago.", "Premium es una suscripción empresarial."],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. Abre el cuaderno de práctica con el comando de abajo; no necesita cuenta, trabaja con un archivo temporal y una clave falsa. [[n1]]Primero guardas una cuenta con save account. [[n2]]Después guardas una segunda y la marcas como predeterminada. [[n3]]Y por último escribes una función que calcula cuántos minutos libres te quedan en la ventana móvil de veintiocho días.
             [[check]]Cada misión tiene una comprobación que se actualiza sola mientras escribes: busca la marca verde.""",
            [
                Mission(
                    "practica/p5-cuenta.py",
                    [
                        (
                            1,
                            "Guarda una cuenta con `save_account` en un archivo temporal y lee `saved_accounts()`.",
                        ),
                        (2, "Guarda una segunda cuenta, `clase`, y hazla la predeterminada."),
                        (
                            3,
                            "Escribe `minutos_libres(usos, hoy)` para el plan Open: 10 min por ventana móvil de 28 días.",
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
            [T("Un límite de gasto es una decisión de diseño, no un trámite.", "subtitle")],
            ask=reflect(
                "Tu clave API se filtra en un repositorio público. Describe, paso a paso, qué harías y en qué orden.",
                "En el hito V ejecutarás en un QPU real con un presupuesto de un minuto. ¿Qué plan usarías y qué límite fijarías antes de enviar nada?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Cuenta, instancia con su CRN y clave API. [[r2]]save account en tu equipo; en uno público, la clave a mano y luego se borra. [[r3]]Sin instancia, el servicio elige con tus preferencias.
             [[r4]]Y hay cinco planes; si pagas, fija un límite de costo.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "cloud-setup",
        "cloud-setup-invited",
        "cloud-setup-untrusted",
        "save-credentials",
        "initialize-account",
        "classroom-accounts",
        "plans-overview",
        "upgrade-from-open",
        "manage-cost",
    ],
    practice=[
        "Crea tu cuenta en [IBM Quantum Platform](https://quantum.cloud.ibm.com), una instancia del plan Open y guarda tus credenciales con `save_account`.",
        "Ejecuta `QiskitRuntimeService().backends()` y anota qué procesadores tienes disponibles.",
    ],
)

# ------------------------------------------------------------------ 5.2 Hola mundo
HELLO = """from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.fake_provider import FakeBelemV2

# 1. Mapear
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
labels = ["IZ", "IX", "ZI", "XI", "ZZ", "XX"]
observables = [SparsePauliOp(label) for label in labels]

# 2. Optimizar
backend = FakeBelemV2()   # en hardware: QiskitRuntimeService().least_busy(...)
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
isa_circuit = pm.run(qc)
mapped = [obs.apply_layout(isa_circuit.layout) for obs in observables]

# 3. Ejecutar
estimator = Estimator(mode=backend)
estimator.options.resilience_level = 1
estimator.options.default_shots = 5000
job = estimator.run([(isa_circuit, mapped)])

# 4. Posprocesar
values = job.result()[0].data.evs
print(dict(zip(labels, values.round(2).tolist())))"""
s_cierre, a_cierre = resumen(
    [
        "`service.least_busy(simulator=False, operational=True)`",
        "Estimator con `resilience_level=1` y `default_shots`",
        "Bell: $\\langle X\\rangle=\\langle Z\\rangle=0$ en cada qubit, $\\langle XX\\rangle=\\langle ZZ\\rangle=1$",
        "a gran escala: $\\langle Z_0Z_i\\rangle$ decae con la distancia por el ruido",
    ]
)
hola = lesson(
    "p5-hello-world",
    "Hola mundo en un QPU",
    "El primer programa en hardware real: un estado de Bell medido con Estimator, y su versión a escala de utilidad con un GHZ de 100 qubits.",
    [
        "autenticarse y elegir el procesador menos ocupado",
        "ejecutar un Estimator con varios observables en un QPU",
        "interpretar la firma del entrelazamiento y el decaimiento por ruido",
    ],
    [
        beat(
            "intro",
            ("", "Del simulador al hardware"),
            """Ya sabes construir, transpilar y simular. Ahora, el primer programa en un procesador cuántico real, con los cuatro pasos de siempre.
             [[auth]]Solo hace falta instalar el cliente, guardar tus credenciales una vez, [[serv]]y crear el servicio. [[proxy]]Si te conectas a través de un proxy, necesitas la versión cero punto cuarenta y cuatro o superior del cliente.""",
            [
                T("Hola mundo cuántico", "title"),
                Code(
                    """from qiskit_ibm_runtime import QiskitRuntimeService
service = QiskitRuntimeService()""",
                    id="c",
                    hidden=True,
                    norun=True,
                ),
            ],
            [A("show", "c", at="serv")],
        ),
        beat(
            "mapear",
            ("", "1 · Mapear: circuito y observables"),
            """Paso uno: el circuito de Bell, y seis observables de dos qubits: I Z, I X, Z I, X I, Z Z y X X.
             [[zz]]Z Z es una abreviatura del producto tensorial Z por Z: mide Z en los dos qubits a la vez y da información de la correlación entre ellos.
             [[ent]]Si el estado está entrelazado, el valor esperado de Z Z no es el producto de los valores de cada qubit por separado. Cuánto vale cada uno en el estado de Bell lo vas a predecir enseguida.""",
            [
                Code(HELLO, id="c", size=20),
                M(
                    r"\langle Z_1Z_0\rangle\ \neq\ \langle Z_1\rangle\langle Z_0\rangle",
                    id="m",
                    hidden=True,
                    size=36,
                ),
            ],
            [A("hl", "c", at="mapear", range="7-12"), A("show", "m", at="ent")],
        ),
        beat(
            "optimizar",
            ("", "2 · Optimizar"),
            """Paso dos: elegimos el procesador. En hardware, service punto least busy, con simulator igual a False y operational igual a True, devuelve el procesador real menos ocupado.
             [[fake]]Para no esperar en la cola, aquí usamos un backend falso, FakeBelem, con el modo de prueba local; cuando funcione, solo cambias esa línea.
             [[isa]]Transpilamos a un circuito ISA [[layout]]y adaptamos los observables a los qubits físicos que eligió el layout.""",
            [Code(HELLO, id="c", size=20)],
            [
                A("hl", "c", at="optimizar", range="14-15"),
                A("hl", "c", at="isa", range="16-17"),
                A("hl", "c", at="layout", lines=[18]),
            ],
        ),
        beat(
            "ejecutar",
            ("", "3 · Ejecutar"),
            """Paso tres: creamos un Estimator con el backend como modo, [[res]]pedimos nivel de resiliencia uno, que activa mitigación de errores de lectura, [[shots]]y cinco mil disparos.
             [[run]]run devuelve un trabajo. En hardware, job id te da su identificador, para recuperar los resultados más tarde aunque cierres Python: el trabajo espera en una cola.""",
            [Code(HELLO, id="c", size=20)],
            [
                A("hl", "c", at="ejecutar", range="20-21"),
                A("hl", "c", at="res", lines=[22]),
                A("hl", "c", at="shots", lines=[23]),
                A("hl", "c", at="run", lines=[24]),
            ],
        ),
        beat(
            "predice",
            ("", "Antes de leer el resultado"),
            """El trabajo terminó. Antes de mirar los números, apuesta. [[zz]]Para el estado de Bell, ¿cuánto crees que vale el valor esperado de Z Z, [[iz]]y cuánto el de I Z, un solo qubit? Recuerda que Z vale más uno si el qubit sale cero, y menos uno si sale uno.""",
            [
                Circ(2, [G("h", 0), G("cx", 0, 1)], id="q"),
                Row(
                    Box(
                        "def",
                        r"$\langle ZZ\rangle$",
                        T("dos qubits a la vez", "body"),
                        id="a",
                        hidden=True,
                    ),
                    Box(
                        "idea",
                        r"$\langle IZ\rangle$",
                        T("un solo qubit", "body"),
                        id="b",
                        hidden=True,
                    ),
                    gap=24,
                ),
            ],
            [A("show", "a", at="zz"), A("show", "b", at="iz")],
            ask=predict(
                "¿Qué valores esperas, con algo de ruido, para ⟨ZZ⟩ y ⟨IZ⟩?",
                ["⟨ZZ⟩ ≈ 1 y ⟨IZ⟩ ≈ 0", "⟨ZZ⟩ ≈ 0 y ⟨IZ⟩ ≈ 1", "los dos ≈ 1", "los dos ≈ 0"],
                "Anotado. Leamos los resultados y veamos si acertaste.",
            ),
        ),
        beat(
            "resultado",
            ("", "4 · Posprocesar"),
            """Paso cuatro: leemos los valores esperados. Así queda el programa completo, que se ejecuta de verdad en el modo local.
             [[val]]Los cuatro observables de un solo qubit dan cero: cada qubit, por separado, es completamente aleatorio. [[corr]]Pero X X y Z Z dan casi uno: las correlaciones son perfectas, salvo por el ruido. Esa es la firma del entrelazamiento, y la respuesta a tu apuesta.""",
            [
                Code(HELLO, id="c", size=18),
                Out(
                    "{'IZ': 0.02, 'IX': -0.01, 'ZI': 0.02, 'XI': -0.01, 'ZZ': 0.96, 'XX': 0.97}",
                    id="o",
                    hidden=True,
                ),
                Hist(
                    [
                        ["IZ", 0.02],
                        ["IX", -0.01],
                        ["ZI", 0.02],
                        ["XI", -0.01],
                        ["ZZ", 0.96],
                        ["XX", 0.97],
                    ],
                    id="h",
                    hidden=True,
                    h=130,
                    ymax=1.15,
                    ymin=-0.2,
                    digits=2,
                    color="teal",
                ),
            ],
            [
                A("hl", "c", at="resultado", range="26-28"),
                A("show", "o", at="val"),
                A("show", "h", at="val", t=1),
                A("hl", "c", at="corr", lines=[28]),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Interpreta un resultado.""",
            [
                T(
                    "Un estado de dos qubits da $\\langle Z_0\\rangle=0$, $\\langle Z_1\\rangle=0$ y $\\langle Z_1Z_0\\rangle=0$.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué puedes concluir?",
                [
                    "está entrelazado",
                    "no hay correlación en la base Z entre los qubits",
                    "es el estado de Bell",
                ],
                1,
                "Correcto: $\\langle Z_1Z_0\\rangle=\\langle Z_1\\rangle\\langle Z_0\\rangle$, así que no hay correlación en Z. Podría haberla en otra base, pero estos datos no la muestran.",
                wrong=[
                    "No se deduce: falta ver otras bases.",
                    None,
                    "En el estado de Bell, $\\langle ZZ\\rangle=1$.",
                ],
            ),
        ),
        beat(
            "escala",
            ("", "A escala de utilidad"),
            """La investigación real necesita mucho más: circuitos de más de cien qubits y más de mil puertas. La guía repite el experimento con un estado GHZ de cien qubits.
             [[ops]]Los observables son Z cero Z i, para i de uno a noventa y nueve: la correlación entre el qubit cero y cada uno de los demás, cada vez más lejos.
             [[opc]]Se ejecuta con resiliencia uno y desacoplamiento dinámico XY4, configurado con EstimatorOptions.
             [[dec]]Idealmente, todas las correlaciones valen uno. En el hardware, decaen con la distancia: el ruido se acumula a lo largo de la cadena de CNOT.""",
            [
                Code(
                    '''n = 100
qc = QuantumCircuit(n)
qc.h(0)
for i in range(n - 1):
    qc.cx(i, i + 1)
ops = [SparsePauliOp("Z" + "I" * i + "Z" + "I" * (n - 2 - i)) for i in range(n - 1)]

from qiskit_ibm_runtime.options_models import EstimatorOptions
options = EstimatorOptions()
options.resilience_level = 1
options.dynamical_decoupling.enable = True
options.dynamical_decoupling.sequence_type = "XY4"''',
                    id="c",
                    size=21,
                ),
                Hist(
                    [["d=1", 0.993], ["d=2", 0.965], ["d=3", 0.96], ["d=4", 0.938]],
                    id="h",
                    hidden=True,
                    h=120,
                    ymax=1.1,
                    digits=2,
                    color="teal",
                ),
                T(
                    "en local, con 5 qubits en FakeManila: $\\langle Z_0Z_i\\rangle$ = 0,99 → 0,94",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="ops", lines=[6]),
                A("hl", "c", at="opc", range="8-12"),
                A("show", "h", at="dec"),
                A("show", "n", at="dec", t=1),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Sobre el decaimiento.""",
            [
                T(
                    "En el GHZ de 100 qubits, $\\langle Z_0Z_{99}\\rangle$ sale mucho menor que $\\langle Z_0Z_1\\rangle$.",
                    "body",
                )
            ],
            ask=choice(
                "¿Por qué?",
                [
                    "el estado GHZ ideal no correlaciona qubits lejanos",
                    "el ruido se acumula a lo largo de la cadena de CNOT",
                    "Estimator no admite 100 observables",
                ],
                1,
                "Correcto: idealmente todos valen 1; los errores de cada CNOT se suman con la distancia.",
                wrong=[
                    "En el GHZ ideal, todos los $\\langle Z_0Z_i\\rangle=1$.",
                    None,
                    "Los admite sin problema.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. Abre el cuaderno de práctica con el comando de abajo; corre en un procesador falso de cinco qubits, sin cuenta. [[n1]]Primero reproduces el estado de Bell con sus seis observables. [[n2]]Después subes los disparos hasta que el error estándar de Z Z baje de cuatro milésimas. [[n3]]Y por último escribes una función que mide las correlaciones de un GHZ de dos a cinco qubits, los que caben en el procesador falso.
             [[check]]Cada misión tiene una comprobación que se actualiza sola mientras escribes: busca la marca verde.""",
            [
                Mission(
                    "practica/p5-hello-world.py",
                    [
                        (1, "Ejecuta el Bell con seis observables y lee `evs`."),
                        (
                            2,
                            r"Sube `default_shots` hasta que el error estándar de $\langle ZZ\rangle$ sea menor que $0{,}004$.",
                        ),
                        (
                            3,
                            r"Escribe `correlaciones(n)` para $\langle Z_0Z_i\rangle$ de un GHZ de 2 a 5 qubits y mira cómo decae con la distancia.",
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
            [T("Un número sin su incertidumbre es solo la mitad del resultado.", "subtitle")],
            ask=reflect(
                "En el Bell, ⟨IZ⟩ y ⟨ZI⟩ valen casi cero mientras ⟨ZZ⟩ vale casi uno. Explica con tus palabras por qué esto no es una contradicción.",
                "Tu proyecto mide la magnetización de una cadena de espines. ¿Qué observables necesitarías pasar a Estimator, y cuántos disparos pedirías para que el error fuera menor que una centésima?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]least busy elige un procesador real. [[r2]]Estimator, con resiliencia y disparos, ejecuta el trabajo. [[r3]]El estado de Bell muestra correlaciones perfectas con qubits individuales aleatorios.
             [[r4]]Y a gran escala, el ruido hace decaer las correlaciones con la distancia.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["hello-world"],
    practice=[
        "Cambia `FakeBelemV2()` por `service.least_busy(simulator=False, operational=True)` y ejecuta el programa en un QPU real (consume segundos del plan Open).",
        "Repite el GHZ con 5 qubits en `FakeManilaV2` y grafica $\\langle Z_0Z_i\\rangle$ frente a $i$.",
    ],
)

# ------------------------------------------------------------------ 5.3 Primitivas de IBM y opciones
s_cierre, a_cierre = resumen(
    [
        "Estimator · Sampler · Executor (beta, bajo nivel)",
        "desde 0.50: Sampler y Estimator del lado del cliente (`executor_sampler`, `executor_estimator`)",
        "opciones: clase, diccionario, atributos o `update()` · `None` = valor por defecto",
        "modelo de ejecución dirigida: cajas anotadas + samplex + Executor + NoiseLearnerV3",
    ]
)
opciones = lesson(
    "p5-opciones",
    "Primitivas de IBM y sus opciones",
    "Estimator, Sampler y Executor; el paso a primitivas del lado del cliente; cómo funcionan las opciones; y el modelo de ejecución dirigida.",
    [
        "distinguir Estimator, Sampler y Executor",
        "configurar opciones de cuatro formas distintas",
        "explicar el modelo de ejecución dirigida",
    ],
    [
        beat(
            "tres",
            ("", "Tres primitivas"),
            """IBM ofrece tres primitivas. [[est]]Estimator calcula valores esperados y trae técnicas de supresión y mitigación de errores incorporadas. [[sam]]Sampler muestrea registros de salida.
             [[exe]]Y Executor, en beta, es de más bajo nivel: muestrea, pero no toma decisiones por ti; a cambio, te da control y transparencia totales, y capacidades que Sampler no tiene, como más grupos de twirling o twirling con puertas fraccionales.""",
            [
                Table(
                    ["Primitiva", "Devuelve", "Errores"],
                    [
                        ["Estimator", "valores esperados", "supresión y mitigación incorporadas"],
                        ["Sampler", "muestras de bits", "supresión incorporada (DD, twirling)"],
                        [
                            "Executor (beta)",
                            "muestras (arreglos NumPy)",
                            "tú decides todo: control total",
                        ],
                    ],
                    id="t",
                    stagger=True,
                    size=25,
                )
            ],
            [
                A("item", "t", at="est", i=0),
                A("item", "t", at="sam", i=1),
                A("item", "t", at="exe", i=2),
            ],
        ),
        beat(
            "cliente",
            ("", "Primitivas del lado del cliente"),
            """Un cambio importante en qiskit ibm runtime cero punto cincuenta: Sampler y Estimator pasaron a ser primitivas del lado del cliente. Hacen la mayor parte del pre y posprocesamiento en tu computadora y delegan la ejecución en Executor.
             [[ventajas]]Eso da más transparencia, depuración más rápida, y permite probar la mitigación en local.
             [[import]]Para usarlas, solo cambia la importación: de qiskit ibm runtime import Estimator, a qiskit ibm runtime punto executor estimator import Estimator. Las opciones vienen de options models.""",
            [
                Code(
                    """# antes (servidor):
# from qiskit_ibm_runtime import Estimator, Sampler
# from qiskit_ibm_runtime.options import EstimatorOptions

# desde 0.50 (cliente):
from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.executor_sampler import Sampler
from qiskit_ibm_runtime.options_models import EstimatorOptions, SamplerOptions""",
                    id="c",
                    size=22,
                )
            ],
            [A("hl", "c", at="import", range="6-8")],
        ),
        beat(
            "pred_defecto",
            ("", "Antes de tocar nada"),
            """Creamos un Estimator local y no cambiamos ninguna opción. [[leer]]Solo imprimimos dos: el nivel de resiliencia y el número de disparos por defecto. [[cual]]Apuesta qué valor tiene cada una.""",
            [
                Code(
                    """estimator = Estimator(mode=FakeManilaV2())
print(estimator.options.resilience_level, estimator.options.default_shots)""",
                    id="c",
                    size=26,
                    setup="from qiskit_ibm_runtime.executor_estimator import Estimator\nfrom qiskit_ibm_runtime.fake_provider import FakeManilaV2",
                )
            ],
            [A("hl", "c", at="leer", lines=[2])],
            ask=predict(
                "¿Qué imprime?",
                ["`0 None`", "`1 None`", "`1 4096`", "`None None`"],
                "Anotado. Ejecutémoslo.",
            ),
        ),
        beat(
            "defecto",
            ("", "Lo que valen sin fijar"),
            """Resultado: resilience level vale uno y default shots queda en None. [[vacio]]No todo lo que no fijas es None: algunas opciones traen ya un valor, como el nivel de resiliencia, y otras quedan vacías.
             [[prec]]Con los disparos vacíos manda la precisión por defecto, cero coma cero uno cinco seis dos cinco, que equivale a cuatro mil noventa y seis disparos.""",
            [
                Code(
                    """estimator = Estimator(mode=FakeManilaV2())
print(estimator.options.resilience_level, estimator.options.default_shots)""",
                    id="c",
                    size=26,
                    setup="from qiskit_ibm_runtime.executor_estimator import Estimator\nfrom qiskit_ibm_runtime.fake_provider import FakeManilaV2",
                ),
                Out("1 None", id="o", check=True),
                M(
                    r"\text{default\_precision}=0{,}015625=\frac{1}{\sqrt{4096}}",
                    id="m",
                    hidden=True,
                    size=34,
                ),
            ],
            [A("hl", "c", at="vacio", lines=[2]), A("show", "m", at="prec")],
        ),
        beat(
            "estructura",
            ("", "Estructura de las opciones"),
            """Las opciones tienen estructura de árbol. Las más usadas, como resilience level, están en el primer nivel; las demás se agrupan en categorías, como execution o dynamical decoupling.
             [[formato]]Se escriben así: options punto opción punto subopción igual a valor. [[unset]]Una opción sin fijar puede valer None, y entonces se usa su valor por defecto, que a veces depende del nivel de resiliencia.""",
            [
                Code(
                    """estimator.options.resilience_level = 2
estimator.options.dynamical_decoupling.enable = True
estimator.options.resilience.zne.noise_factors = [1, 3, 5]""",
                    id="c",
                    setup="from qiskit_ibm_runtime.executor_estimator import Estimator\nfrom qiskit_ibm_runtime.fake_provider import FakeManilaV2\n\nestimator = Estimator(mode=FakeManilaV2())",
                ),
                T(
                    "sin fijar → `None` → valor por defecto (a veces según el nivel de resiliencia)",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [A("hl", "c", at="formato", range="2-3"), A("show", "n", at="unset")],
        ),
        beat(
            "formas",
            ("", "Cuatro formas de fijarlas"),
            """Hay cuatro formas. [[clase]]Con una instancia de la clase de opciones, al crear la primitiva. [[dict]]Con un diccionario, también al crearla. En ambos casos la primitiva copia las opciones: cambiar después el original no le afecta.
             [[attr]]Asignando atributos después de crearla, con autocompletado. [[update]]O con update, para cambiar varias de golpe. [[dump]]Y como options es un modelo de pydantic, model dump lo convierte en diccionario.""",
            [
                Code(
                    """from qiskit_ibm_runtime.fake_provider import FakeManilaV2

backend = FakeManilaV2()
options = EstimatorOptions()
options.resilience_level = 2
options.resilience.zne_mitigation = True
estimator = Estimator(mode=backend, options=options)                 # clase
estimator = Estimator(mode=backend, options={"resilience_level": 2}) # diccionario
estimator.options.default_precision = 0.01                           # atributo
estimator.options.update(default_precision=0.02,
                         resilience={"zne_mitigation": True})       # update
print(estimator.options.default_precision, list(estimator.options.model_dump())[:4])""",
                    id="c",
                    size=20,
                ),
                Out(
                    "0.02 ['default_precision', 'default_shots', 'execution', 'twirling']",
                    id="o",
                    hidden=True,
                    check=True,
                ),
            ],
            [
                A("hl", "c", at="clase", range="4-7"),
                A("hl", "c", at="dict", lines=[8]),
                A("hl", "c", at="attr", lines=[9]),
                A("hl", "c", at="update", range="10-11"),
                A("hl", "c", at="dump", lines=[12]),
                A("show", "o", at="dump"),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Sobre la copia de opciones.""",
            [
                Code("""opts = {"resilience_level": 1}
estimator = Estimator(mode=backend, options=opts)
opts["resilience_level"] = 2""")
            ],
            ask=choice(
                "¿Qué nivel de resiliencia usa el estimator?",
                ["1", "2"],
                0,
                "Correcto: la primitiva copia las opciones al crearse. Para cambiarlas, usa `estimator.options`.",
                wrong=[
                    "Cambiar el diccionario original no afecta a la copia que guardó la primitiva."
                ],
            ),
        ),
        beat(
            "dirigida",
            ("", "El modelo de ejecución dirigida"),
            """Sampler y Estimator son ideales para desarrollar algoritmos, pero los científicos que hacen experimentos a gran escala necesitan más control. Para ellos existe el modelo de ejecución dirigida, en beta.
             [[pasos]]El flujo tiene cuatro pasos. Agrupas instrucciones en cajas y les pones anotaciones, que expresan la intención, por ejemplo twirling, sin generar todavía las variantes del circuito.
             [[build]]Construyes un circuito plantilla y un samplex, que describe cómo aleatorizar sus parámetros. [[run]]Executor genera y ejecuta las variantes en el servidor. [[post]]Y tú posprocesas: postselección, extrapolación, lo que necesites.
             [[nl]]Si hace falta, NoiseLearnerV3 aprende primero el modelo de ruido de las capas.""",
            [
                Flow(
                    [
                        dict(t="Cajas anotadas", s="Samplomatic"),
                        dict(t="Plantilla + samplex", s="`build()`"),
                        dict(t="Executor", s="variantes en el servidor"),
                        dict(t="Posprocesar", s="postselección, ZNE…"),
                    ],
                    id="f",
                    stagger=True,
                    numbered=True,
                ),
                T(
                    "opcional: NoiseLearnerV3 aprende el ruido de cada capa (modelo de Pauli–Lindblad y TREX)",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [
                A("item", "f", at="pasos", i=0),
                A("item", "f", at="build", i=1),
                A("item", "f", at="run", i=2),
                A("item", "f", at="post", i=3),
                A("show", "n", at="nl"),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Elige la herramienta.""",
            [
                T(
                    "Quieres decidir exactamente qué capas del circuito se mitigan y con qué ruido inyectado.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué usas?",
                [
                    "Estimator con `resilience_level=2`",
                    "el modelo de ejecución dirigida con Executor",
                    "Sampler con twirling",
                ],
                1,
                "Correcto: la ejecución dirigida permite elegir capas a mitigar y ajustar las tasas de ruido inyectadas.",
                wrong=[
                    "Los niveles de resiliencia deciden por ti.",
                    None,
                    "Sampler no ofrece ese control fino.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. Abre el cuaderno de práctica con el comando de abajo; corre con un procesador falso, sin cuenta. [[n1]]Primero fijas la misma precisión de cuatro formas distintas. [[n2]]Después corriges un error típico: cambiar las opciones del objeto equivocado. [[n3]]Y por último escribes una función que crea un Estimator crudo o protegido, y comparas el valor de Z Z que da cada uno.
             [[check]]Cada misión tiene una comprobación que se actualiza sola mientras escribes: busca la marca verde.""",
            [
                Mission(
                    "practica/p5-opciones.py",
                    [
                        (
                            1,
                            "Fija `default_precision = 0.02` con clase, diccionario, atributo y `update`.",
                        ),
                        (
                            2,
                            "Arregla el código para que cambiar los disparos afecte al `Estimator` ya creado.",
                        ),
                        (
                            3,
                            'Escribe `crear_estimator("crudo" | "protegido")` y compara su $\\langle ZZ\\rangle$.',
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
            [T("Más control también es más responsabilidad.", "subtitle")],
            ask=reflect(
                "Cuatro formas de fijar una opción parecen demasiadas. ¿Cuál usarías en un script largo y cuál en una exploración rápida? ¿Por qué?",
                "En tu proyecto, ¿preferirías Estimator con un nivel de resiliencia o el modelo de ejecución dirigida? Justifica con lo que necesitas controlar.",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Estimator, Sampler y Executor, de más alto a más bajo nivel. [[r2]]Desde la cero punto cincuenta, Sampler y Estimator corren del lado del cliente. [[r3]]Las opciones se fijan con clase, diccionario, atributos o update.
             [[r4]]Y la ejecución dirigida te da control total sobre la mitigación.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=["qiskit-runtime-primitives", "runtime-options-overview", "directed-execution-model"],
    practice=[
        "Crea un `Estimator` local con `FakeManilaV2`, imprime `estimator.options.model_dump()` y busca qué opciones siguen en `None`.",
        "Lee la guía de [Samplomatic](https://quantum.cloud.ibm.com/docs/en/addons/samplomatic) para conocer los tipos de anotaciones.",
    ],
)

# ------------------------------------------------------------------ 5.4 Estimator
# Context of the fragments: a local two-qubit backend, an already transpiled circuit with two parameters and its Estimator.
EST_SETUP = """import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_estimator import Estimator

backend = GenericBackendV2(2, basis_gates=["cz", "rz", "sx", "x"], seed=1)
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
a, b = Parameter("a"), Parameter("b")
circuit = QuantumCircuit(2)
circuit.rx(a, 0)
circuit.ry(b, 1)
circuit.cx(0, 1)
transpiled_circuit = pm.run(circuit)
estimator = Estimator(mode=backend)
bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)
qc1 = qc2 = pm.run(bell)
obs1 = obs2 = SparsePauliOp("ZZ")"""
EST_ENTRADAS = """params = np.vstack([np.linspace(-np.pi, np.pi, 100),
                    np.linspace(-4 * np.pi, 4 * np.pi, 100)]).T
observables = [[SparsePauliOp(["XX", "IY"], [0.5, 0.5])],
               [SparsePauliOp("XX")],
               [SparsePauliOp("IY")]]
job = estimator.run([(transpiled_circuit, observables, params)])"""
s_cierre, a_cierre = resumen(
    [
        "`Estimator(mode=backend | batch | session)` · PUB (circuito, observables, parámetros, precisión)",
        "`data`: `evs`, `stds`, `ensemble_standard_error` · `metadata` con opciones usadas",
        "precisión: PUB > `run()` > twirling > `default_shots` > `default_precision`",
        "`resilience_level` 0, 1 (por defecto) o 2 · algunas técnicas son incompatibles",
    ]
)
estimator = lesson(
    "p5-estimator",
    "Estimator en IBM Quantum",
    "Usar Estimator en hardware: inicialización, entradas y salidas, cómo calcula los errores, la precedencia de la precisión, sus opciones y ejemplos.",
    [
        "ejecutar Estimator en sus tres modos",
        "interpretar `evs`, `stds` y `ensemble_standard_error`",
        "controlar la precisión y las opciones de resiliencia",
    ],
    [
        beat(
            "pasos",
            ("", "Cuatro pasos"),
            """Usar Estimator tiene cuatro pasos. [[serv]]Inicializar la cuenta y elegir un procesador. Para puertas fraccionales, pide el backend con use fractional gates igual a True.
             [[circ]]Crear circuito y observable, y transpilarlos a ISA. [[init]]Crear el Estimator con un modo: un backend, para un trabajo suelto; un batch, para un lote; o una sesión. [[run]]Y llamar a run con los PUBs.""",
            [
                Code(
                    """backend = service.least_busy(operational=True, simulator=False, min_num_qubits=127)
# fraccionales: service.least_busy(use_fractional_gates=True)

isa_circuit = pm.run(circuit)
isa_observable = observable.apply_layout(isa_circuit.layout)

estimator = Estimator(mode=backend)      # o mode=batch / mode=session
job = estimator.run([(isa_circuit, isa_observable, param_values)])
print(job.job_id(), job.status())""",
                    id="c",
                    norun=True,
                    size=22,
                )
            ],
            [
                A("hl", "c", at="serv", range="1-2"),
                A("hl", "c", at="circ", range="4-5"),
                A("hl", "c", at="init", lines=[7]),
                A("hl", "c", at="run", range="8-9"),
            ],
        ),
        beat(
            "entradas",
            ("", "Entradas"),
            """Las entradas son PUBs, como ya sabes: circuito, observables, parámetros y precisión. Si el circuito trae mediciones, se ignoran.
             [[agrupar]]Los observables que conmutan dentro del mismo PUB se agrupan para medirse juntos, por conmutación qubit a qubit. En PUBs distintos, no.
             [[ej]]El ejemplo de la guía: un circuito con dos parámetros, cien juegos de valores y tres observables en forma tres por uno, todo en una sola llamada.""",
            [Code(EST_ENTRADAS, id="c", size=22, norun=True)],
            [A("hl", "c", at="agrupar", range="3-5"), A("hl", "c", at="ej", lines=[6])],
        ),
        beat(
            "pred_forma",
            ("", "Antes de ejecutar"),
            """Cuenta bien las formas de lo que entra. [[par]]Los parámetros tienen forma cien por dos: cien juegos de dos valores, así que el barrido es de cien. [[obs]]Los observables, tres por uno.
             [[cual]]Apuesta: ¿qué forma tendrá el arreglo de valores esperados, evs?""",
            [Code(EST_ENTRADAS, id="c", size=22, norun=True)],
            [A("hl", "c", at="par", range="1-2"), A("hl", "c", at="obs", range="3-5")],
            ask=predict(
                "¿Qué forma tiene `evs`?",
                ["`(3, 100)`", "`(100, 3)`", "`(300,)`", "`(3, 1, 100)`"],
                "Anotado. Ejecutémoslo y miremos la forma.",
            ),
        ),
        beat(
            "forma",
            ("", "Broadcasting de PUBs"),
            """Resultado: tres por cien. [[bc]]Los observables, de forma tres por uno, y el barrido de parámetros, de forma cien, se alinean por la derecha y se combinan por broadcasting: tres filas, una por observable, y cien columnas, una por juego de parámetros.
             [[tot]]Son trescientos valores esperados en una sola llamada.""",
            [
                Code(
                    EST_ENTRADAS + "\nprint(job.result()[0].data.evs.shape)",
                    id="c",
                    setup=EST_SETUP,
                    size=20,
                ),
                Out("(3, 100)", id="o", check=True),
                M(r"(3,1)\ \text{con}\ (100,)\ \Rightarrow\ (3,100)", id="m", hidden=True, size=36),
            ],
            [
                A("hl", "c", at="bc", lines=[6]),
                A("show", "m", at="bc"),
                A("hl", "c", at="tot", lines=[7]),
            ],
        ),
        beat(
            "salidas",
            ("", "Salidas"),
            """La salida es la misma estructura que ya conoces: un PubResult por PUB, con data y metadata. [[data]]En data están evs, los valores esperados; stds, sus desviaciones; y ensemble standard error. Según la mitigación, puede haber más.
             [[meta]]La metadata del PrimitiveResult recoge las opciones usadas: desacoplamiento dinámico, twirling, resiliencia. La de cada PUB, los disparos, la precisión objetivo y el número de aleatorizaciones.
             [[local]]Estas son las claves reales del resultado del trabajo anterior, ejecutado en local.""",
            [
                Code(
                    """res = job.result()[0]
print(list(res.data.keys()))""",
                    id="c",
                ),
                Out("['evs', 'stds', 'ensemble_standard_error']", id="o", hidden=True, check=True),
                Code(
                    """metadata: {'shots': 4096, 'target_precision': 0.015625, 'resilience': {}, 'num_randomizations': 32}""",
                    "out",
                    id="m",
                    hidden=True,
                ),
            ],
            [A("show", "o", at="data"), A("show", "m", at="meta")],
        ),
        beat(
            "errores",
            ("", "Cómo calcula el error"),
            """Además del valor medio, Estimator estima su error. Sin extrapolación a ruido cero, cada disparo es una estimación puntual; stds es la desviación estándar de esas estimaciones dividida entre la raíz del número de disparos.
             [[twirl]]Si hay twirling de puertas, las estimaciones se agrupan por cada twirl, y ensemble standard error divide la desviación entre esos grupos por la raíz del número de twirls. Sin twirling, las dos cantidades coinciden.
             [[zne]]Con ZNE, el error que se reporta es la incertidumbre del ajuste evaluado en ruido cero; si el ajuste es malo, puede ser enorme.""",
            [
                Row(
                    Box(
                        "def",
                        "`stds`",
                        M(r"\frac{\sigma_{\mathcal O}}{\sqrt{N_{\text{disparos}}}}", size=40),
                    ),
                    Box(
                        "idea",
                        "`ensemble_standard_error`",
                        M(r"\frac{\sigma_{\text{twirls}}}{\sqrt{N_{\text{twirls}}}}", size=40),
                        id="b",
                        hidden=True,
                    ),
                    gap=30,
                ),
                T("con ZNE: incertidumbre del ajuste en ruido cero", "note", id="n", hidden=True),
            ],
            [A("show", "b", at="twirl"), A("show", "n", at="zne")],
        ),
        beat(
            "precision",
            ("", "¿Cuántos disparos?"),
            """La precisión se puede indicar en varios sitios, y gana el primero de esta lista. [[pub]]Uno: la precisión dentro del PUB. [[run]]Dos: el argumento precision de run.
             [[tw]]Tres: si el twirling está activo, que lo está por defecto, el número de aleatorizaciones por los disparos de cada una. [[shots]]Cuatro: default shots. [[prec]]Cinco: default precision, que por defecto es uno sobre la raíz de cuatro mil noventa y seis.
             [[falla]]Cuidado: si pides una precisión que necesita más disparos de los que permite la configuración de twirling, el trabajo falla. Y recuerda: más precisión, más tiempo de QPU.
             [[uno]]Y un detalle de la cero punto cincuenta: todos los PUBs de un mismo trabajo deben tener la misma precisión; si mezclas, da error.""",
            [
                Table(
                    ["Prioridad", "Dónde"],
                    [
                        ["1", "precisión dentro del PUB"],
                        ["2", "`run(..., precision=)`"],
                        ["3", "twirling: `num_randomizations × shots_per_randomization`"],
                        ["4", "`options.default_shots`"],
                        ["5", "`options.default_precision` (0.015625 = $1/\\sqrt{4096}$)"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                ),
                Box(
                    "warn",
                    "qiskit-ibm-runtime 0.50",
                    T(
                        "«All pubs must have the same precision»: una única precisión por trabajo",
                        "body",
                    ),
                    id="b",
                    hidden=True,
                ),
            ],
            [
                A("item", "t", at="pub", i=0),
                A("item", "t", at="run", i=1),
                A("item", "t", at="tw", i=2),
                A("item", "t", at="shots", i=3),
                A("item", "t", at="prec", i=4),
                A("show", "b", at="uno"),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Aplica la precedencia.""",
            [
                Code(
                    """estimator.options.default_precision = 0.05
estimator.run([(qc1, obs1), (qc2, obs2)], precision=0.02)""",
                    setup=EST_SETUP,
                )
            ],
            ask=choice(
                "¿Qué precisión objetivo tienen los PUBs?",
                ["0.05", "0.02", "0.015625"],
                1,
                "Correcto: ningún PUB especifica precisión, así que manda el argumento de `run`, 0.02, que gana a `default_precision`.",
                wrong=[
                    "`run` tiene prioridad sobre `default_precision`.",
                    None,
                    "Ese es el valor por defecto de `default_precision`, y aquí `run` lo anula.",
                ],
            ),
        ),
        beat(
            "opciones",
            ("", "Opciones de Estimator"),
            """Las opciones principales de Estimator. [[res]]resilience level: cero, uno o dos; uno es el valor por defecto, y cero desactiva toda mitigación y supresión, útil si investigas tus propias técnicas.
             [[dd]]dynamical decoupling: activar, y elegir la secuencia, XX, XpXm o XY4. [[tw]]twirling: de puertas y de mediciones, número de aleatorizaciones y estrategia. [[resil]]resilience: mitigación de lectura, ZNE, PEC y sus parámetros, como los factores de ruido o el extrapolador.
             [[exec]]Y execution, environment y max execution time, de uno a diez mil ochocientos segundos, tres horas.""",
            [
                Table(
                    ["Opción", "Valores"],
                    [
                        ["`resilience_level`", "0 · **1** · 2"],
                        ["`dynamical_decoupling`", "`enable` · `sequence_type`: XX, XpXm, XY4"],
                        [
                            "`twirling`",
                            "`enable_gates` · `enable_measure` · `num_randomizations` · `strategy`",
                        ],
                        [
                            "`resilience`",
                            "`measure_mitigation` · `zne_mitigation` (`noise_factors`, `extrapolator`) · `pec_mitigation`",
                        ],
                        [
                            "`execution` · `environment`",
                            "`init_qubits`, `rep_delay` · `log_level`, `job_tags`",
                        ],
                        ["`max_execution_time`", "1 – 10 800 s"],
                    ],
                    id="t",
                    stagger=True,
                    size=21,
                )
            ],
            [
                A("item", "t", at="res", i=0),
                A("item", "t", at="dd", i=1),
                A("item", "t", at="tw", i=2),
                A("item", "t", at="resil", i=3),
                A("item", "t", at="exec", i=4),
                A("item", "t", at="exec", t=2, i=5),
            ],
        ),
        beat(
            "compat",
            ("", "Técnicas incompatibles"),
            """No todas las técnicas se combinan en un mismo trabajo. [[dd]]El desacoplamiento dinámico es incompatible con las puertas fraccionales y con stretch.
             [[tw]]El twirling de puertas no funciona con entrelazadores que no sean de Clifford, y el de mediciones solo se aplica a mediciones finales. [[pea]]PEA no se combina con puertas fraccionales, ZNE por plegado de puertas ni PEC.
             [[pec]]Y PEC tampoco con fraccionales, ZNE por plegado ni PEA.""",
            [
                Table(
                    ["Técnica", "Incompatible con"],
                    [
                        ["Desacoplamiento dinámico", "puertas fraccionales · stretch"],
                        ["Twirling", "entrelazadores no Clifford · medición solo al final"],
                        ["PEA", "fraccionales · ZNE por plegado · PEC"],
                        ["PEC", "fraccionales · ZNE por plegado · PEA"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                )
            ],
            [
                A("item", "t", at="dd", i=0),
                A("item", "t", at="tw", i=1),
                A("item", "t", at="pea", i=2),
                A("item", "t", at="pec", i=3),
            ],
        ),
        beat(
            "chsh",
            ("", "Ejemplo: la desigualdad CHSH"),
            """Un ejemplo de la guía: el experimento CHSH. Un circuito de Bell con una rotación RY de ángulo theta, veintiún valores de theta entre cero y dos pi, y cuatro observables, ZZ, ZX, XZ y XX.
             [[forma]]Los observables en forma cuatro por uno y los ángulos en forma veintiuno por uno dan ochenta y cuatro valores esperados en un solo trabajo.
             [[res]]En el hardware, las cuatro curvas oscilan entre menos uno y uno, desfasadas: con ellas se demuestra la violación de la desigualdad de Bell.""",
            [
                Code(
                    """theta = Parameter("θ")
chsh = QuantumCircuit(2)
chsh.h(0)
chsh.cx(0, 1)
chsh.ry(theta, 0)
phases = [[ph] for ph in np.linspace(0, 2 * np.pi, 21)]              # (21, 1)
ops = np.fromiter([SparsePauliOp(p) for p in ["ZZ", "ZX", "XZ", "XX"]],
                  dtype=object).reshape((4, 1))                      # (4, 1)
chsh_isa = pm.run(chsh)
isa_ops = [[op.apply_layout(chsh_isa.layout)] for op in ops.flat]
estimator = Estimator(backend, options={"default_shots": int(1e4)})
job = estimator.run([(chsh_isa, isa_ops, phases)])                   # evs: (4, 21)""",
                    id="c",
                    setup=EST_SETUP,
                    size=21,
                ),
                T(
                    "evs: forma (4, 21) · cuatro curvas desfasadas entre −1 y 1",
                    "note",
                    id="n",
                    hidden=True,
                ),
            ],
            [A("hl", "c", at="forma", range="6-8"), A("show", "n", at="res")],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Sobre resiliencia.""",
            [
                T(
                    "Estás probando tu propia técnica de mitigación y quieres los datos sin ninguna corrección de IBM.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué fijas?",
                ["`resilience_level = 0`", "`resilience_level = 1`", "`resilience_level = 2`"],
                0,
                "Correcto: el nivel 0 desactiva toda la mitigación y la supresión.",
                wrong=[
                    None,
                    "El nivel 1 aplica mitigación de lectura.",
                    "El nivel 2 aplica aún más mitigación.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. Abre el cuaderno de práctica con el comando de abajo; corre con un procesador falso de cinco qubits, sin cuenta. [[n1]]Primero reproduces el barrido de trescientos valores esperados. [[n2]]Después cambias una sola línea para bajar el error estándar de Z Z. [[n3]]Y por último escribes la función que combina los cuatro observables del experimento CHSH en el valor S.
             [[check]]Cada misión tiene una comprobación que se actualiza sola mientras escribes: busca la marca verde.""",
            [
                Mission(
                    "practica/p5-estimator.py",
                    [
                        (
                            1,
                            "Ejecuta un barrido de 100 juegos de parámetros con 3 observables y lee la forma de `evs`.",
                        ),
                        (
                            2,
                            r"Baja el error estándar de $\langle ZZ\rangle$ de $0{,}008$ cambiando una sola línea.",
                        ),
                        (3, r"Escribe `valor_S(evs)` para CHSH y comprueba que $|S|>2$."),
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
            [T("Cada centésima de precisión se paga con tiempo de procesador.", "subtitle")],
            ask=reflect(
                "La precisión por defecto equivale a 4096 disparos. Para duplicar la precisión, ¿cuántos disparos necesitas? ¿Qué implica eso para un presupuesto de QPU?",
                "Tu proyecto mide la magnetización. ¿La mandarías como un solo observable o como varios PUBs? Piensa en cuántos circuitos distintos se ejecutarán.",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Estimator recibe PUBs y un modo. [[r2]]Devuelve evs, stds y ensemble standard error, más metadata. [[r3]]La precisión sigue una cadena de prioridades.
             [[r4]]Y resilience level resume la mitigación, aunque no todas las técnicas se combinan.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "get-started-with-estimator",
        "estimator-input-output",
        "estimator-options",
        "estimator-examples",
    ],
    practice=[
        "Ejecuta el ejemplo CHSH en local con `FakeManilaV2` y grafica las cuatro curvas.",
        "Calcula $S=\\langle ZZ\\rangle-\\langle ZX\\rangle+\\langle XZ\\rangle+\\langle XX\\rangle$ y busca el ángulo donde $|S|>2$.",
    ],
)

# ------------------------------------------------------------------ 5.5 Sampler
# Context of the examples fragment: a local backend, already transpiled circuits and an ansatz with three sets of parameters.
SAMPLER_SETUP = """import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import real_amplitudes
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime import Batch
from qiskit_ibm_runtime.executor_sampler import Sampler
from qiskit_ibm_runtime.fake_provider import FakeBelemV2

backend = FakeBelemV2()
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
ghz = QuantumCircuit(3)
ghz.h(0)
ghz.cx(0, 1)
ghz.cx(1, 2)
ghz.measure_all()
isa_circuit = pm.run(ghz)
another_isa_circuit = isa_circuit.copy()
isa_circuits = [isa_circuit, another_isa_circuit]
ansatz = real_amplitudes(3, reps=1)
ansatz.measure_all()
isa_ansatz = pm.run(ansatz)
parameter_values = np.random.rand(3, ansatz.num_parameters)
sampler = Sampler(mode=backend)"""
s_cierre, a_cierre = resumen(
    [
        "`Sampler(mode=…)` · PUB (circuito con mediciones, parámetros, disparos)",
        "un `BitArray` por registro · `chunk_timing` en la metadata con los intervalos de ejecución",
        "disparos: PUB > `run()` > twirling > `default_shots` · en 0.50, todos los PUBs igual",
        "opciones: DD, twirling, `meas_type`, `max_execution_time` (sin `resilience_level`)",
    ]
)
sampler = lesson(
    "p5-sampler",
    "Sampler en IBM Quantum",
    "Usar Sampler en hardware: entradas y salidas, intervalos de ejecución, precedencia de los disparos, opciones e incompatibilidades.",
    [
        "ejecutar Sampler con circuitos parametrizados",
        "leer intervalos de ejecución en la metadata",
        "controlar los disparos y las opciones de Sampler",
    ],
    [
        beat(
            "pasos",
            ("", "Usar Sampler"),
            """Sampler sigue los mismos pasos que Estimator. Acepta circuitos parametrizados y también circuitos dinámicos.
             [[circ]]El circuito debe tener mediciones: aquí, un efficient su2 de ciento veintisiete qubits con measure all. [[tr]]Se transpila a ISA, [[run]]y se ejecuta con sus valores de parámetros.
             [[res]]get bitstrings devuelve las cadenas de bits en orden: cada una tiene ciento veintisiete caracteres.""",
            [
                Code(
                    """circuit = efficient_su2(127, entanglement="linear")
circuit.measure_all()
param_values = np.random.rand(circuit.num_parameters)
isa_circuit = generate_preset_pass_manager(optimization_level=1, backend=backend).run(circuit)

sampler = Sampler(mode=backend)
job = sampler.run([(isa_circuit, param_values)])
print(job.result()[0].data.meas.get_bitstrings()[:10])""",
                    id="c",
                    norun=True,
                    size=22,
                )
            ],
            [
                A("hl", "c", at="circ", range="1-3"),
                A("hl", "c", at="tr", lines=[4]),
                A("hl", "c", at="run", range="6-7"),
                A("hl", "c", at="res", lines=[8]),
            ],
        ),
        beat(
            "salidas",
            ("", "Entradas y salidas"),
            """El PUB de Sampler tiene circuito, parámetros y disparos. La salida, un SamplerPubResult por PUB, con un BitArray por registro clásico.
             [[ruido]]En hardware, un GHZ de diez qubits ya no da solo ceros y unos: aparecen muchas cadenas con algún bit cambiado por el ruido. Por ejemplo, mil seiscientas ochenta veces todos ceros, mil cuatrocientas sesenta y siete todos unos, y el resto repartido.
             [[post]]Todo el posprocesamiento con BitArray que viste en la Parte cuatro funciona igual.""",
            [
                Hist(
                    [
                        ["0000000000", 1680],
                        ["1111111111", 1467],
                        ["1111111110", 119],
                        ["0000000001", 66],
                        ["1000000000", 52],
                        ["otros", 712],
                    ],
                    id="h",
                    h=170,
                    w=820,
                    color="blue",
                    grow=True,
                ),
                T("ejemplo de la guía: GHZ de 10 qubits en un QPU real, 4096 disparos", "note"),
            ],
            [A("grow", "h", at="ruido")],
        ),
        beat(
            "spans",
            ("", "Intervalos de ejecución"),
            """Los resultados de Sampler en un QPU incluyen información de tiempos: los intervalos de ejecución.
             [[que]]Con el Sampler del lado del cliente de la cero punto cincuenta, están en la metadata del Executor, como chunk timing: una lista de intervalos que envuelve ChunkTiming.
             [[partes]]Cada intervalo tiene un inicio, un fin y sus partes: de cada una, el índice del PUB y cuántos elementos se ejecutaron en ese intervalo.
             [[util]]start, stop y duration dan los tiempos globales, y draw dibuja los intervalos en una gráfica.
             [[ojo]]Los intervalos pueden solaparse: no porque el QPU haga dos cosas a la vez, sino por procesamiento clásico concurrente.""",
            [
                Code(
                    """from qiskit_ibm_runtime.results import ChunkTiming

chunks = job.result().metadata["executor"].chunk_timing
timing = ChunkTiming(chunks)
print(len(timing), timing.start, timing.stop, timing.duration)
for part in timing[0].parts:                 # PUBs de este intervalo
    print(part.idx_item, part.size)
timing.draw()""",
                    id="c",
                    norun=True,
                    size=22,
                )
            ],
            [
                A("hl", "c", at="que", range="3-4"),
                A("hl", "c", at="partes", range="6-7"),
                A("hl", "c", at="util", lines=[5, 8]),
            ],
        ),
        beat(
            "pred_shots",
            ("", "¿Cuántos disparos?"),
            """Un Sampler con dos fuentes de disparos que no coinciden. [[def]]Fijamos default shots en quinientos. [[run]]Pero al llamar a run pedimos ciento veintiocho. [[cual]]Apuesta: ¿cuántos disparos recibirá cada PUB?""",
            [
                Code(
                    """sampler.options.default_shots = 500
result = sampler.run([isa, isa], shots=128).result()
print([pub.data.meas.num_shots for pub in result])""",
                    id="c",
                    size=26,
                    norun=True,
                )
            ],
            [A("hl", "c", at="def", lines=[1]), A("hl", "c", at="run", lines=[2])],
            ask=predict(
                "¿Qué imprime?",
                ["`[500, 500]`", "`[128, 128]`", "`[500, 128]`", "`[4096, 4096]`"],
                "Anotado. Veamos en qué orden se aplican las fuentes de disparos.",
            ),
        ),
        beat(
            "shots",
            ("", "Los disparos"),
            """Para los disparos la precedencia es como la de la precisión en Estimator. [[pub]]Primero, los del PUB; [[run]]luego, el argumento shots de run, que es lo que decide tu apuesta; [[tw]]luego, si hay twirling, aleatorizaciones por disparos de cada una; [[def]]y al final default shots.
             [[cliente]]Un detalle que descubrimos al probar el código: con el Sampler del lado del cliente de la cero punto cincuenta, todos los PUBs de un mismo trabajo deben tener el mismo número de disparos. Si mezclas, por ejemplo sesenta y cuatro y ciento veintiocho, da error.""",
            [
                Table(
                    ["Prioridad", "Dónde"],
                    [
                        ["1", "dentro del PUB"],
                        ["2", "`run(..., shots=)`"],
                        ["3", "twirling"],
                        ["4", "`options.default_shots`"],
                    ],
                    id="t",
                    stagger=True,
                    size=25,
                ),
                Box(
                    "warn",
                    "qiskit-ibm-runtime 0.50",
                    T(
                        "«All pubs must have the same number of shots»: un único número de disparos por trabajo",
                        "body",
                    ),
                    id="b",
                    hidden=True,
                ),
            ],
            [
                A("item", "t", at="pub", i=0),
                A("item", "t", at="run", i=1),
                A("item", "t", at="tw", i=2),
                A("item", "t", at="def", i=3),
                A("show", "b", at="cliente"),
            ],
        ),
        beat(
            "local",
            ("", "Probarlo en local"),
            """Lo comprobamos en local: dos PUBs con default shots quinientos y shots ciento veintiocho en run. [[res]]Cada uno recibe ciento veintiocho: run gana a default shots.""",
            [
                Code(
                    """from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_sampler import Sampler
from qiskit_ibm_runtime.fake_provider import FakeBelemV2

backend = FakeBelemV2()
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()
isa = generate_preset_pass_manager(backend=backend, optimization_level=1).run(qc)
sampler = Sampler(mode=backend)
sampler.options.default_shots = 500
result = sampler.run([isa, isa], shots=128).result()
print([pub.data.meas.num_shots for pub in result])""",
                    id="c",
                    size=21,
                ),
                Out("[128, 128]", id="o", hidden=True, check=True),
            ],
            [A("hl", "c", at="local", range="13-14"), A("show", "o", at="res")],
        ),
        beat(
            "opciones",
            ("", "Opciones de Sampler"),
            """Las opciones de Sampler son parecidas a las de Estimator, pero sin resilience level: en Sampler activas o desactivas cada técnica por separado.
             [[dd]]Desacoplamiento dinámico, con sus secuencias. [[tw]]Twirling, de puertas y de mediciones; en Sampler, el de mediciones está desactivado por defecto. [[meas]]Y en execution, meas type: classified, la opción normal, que devuelve bits; kerneled o avg kerneled, que devuelven los datos analógicos de la medición.
             [[compat]]Algunas incompatibilidades propias: el desacoplamiento dinámico no se combina con twirling de puertas, y el twirling de mediciones no funciona con la instrucción store.""",
            [
                Table(
                    ["Opción", "Valores"],
                    [
                        ["`dynamical_decoupling`", "`enable` · XX, XpXm, XY4"],
                        ["`twirling`", "`enable_gates` · `enable_measure` (falso por defecto)"],
                        ["`execution.meas_type`", "`classified` · `kerneled` · `avg_kerneled`"],
                        ["`max_execution_time`", "1 – 10 800 s"],
                    ],
                    id="t",
                    stagger=True,
                    size=24,
                ),
                T(
                    "DD ✕ twirling de puertas · twirling de medición ✕ `store`",
                    "note",
                    id="n",
                    hidden=True,
                    color="red",
                ),
            ],
            [
                A("item", "t", at="dd", i=0),
                A("item", "t", at="tw", i=1),
                A("item", "t", at="meas", i=2),
                A("item", "t", at="meas", t=3, i=3),
                A("show", "n", at="compat"),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Una pregunta sobre Sampler.""",
            [Code("sampler.options.resilience_level = 1", norun=True)],
            ask=choice(
                "¿Qué pasa?",
                [
                    "activa la mitigación de lectura",
                    "no tiene sentido: Sampler no tiene `resilience_level`",
                    "desactiva el twirling",
                ],
                1,
                "Correcto: Sampler no admite niveles de resiliencia; activas cada técnica de supresión por separado. En la 0.50 la asignación lanza un `ValidationError`.",
                wrong=["Eso es de Estimator.", None, "No existe esa opción en Sampler."],
            ),
        ),
        beat(
            "ejemplos",
            ("", "Ejemplos"),
            """Los ejemplos de la guía cubren los casos típicos: un experimento con un circuito IQP de ciento veintisiete qubits; [[multi]]varios circuitos en un solo trabajo, pasándolos como lista; [[par]]un circuito parametrizado, real amplitudes, con tres juegos de parámetros en un PUB;
             [[batch]]y dos trabajos dentro de un lote, con with Batch, que se cierra solo al salir del bloque.""",
            [
                Code(
                    """job = sampler.run([isa_circuit])                          # uno
job = sampler.run(isa_circuits)                            # varios
job = sampler.run([(isa_ansatz, parameter_values)])        # 3 juegos de parámetros
with Batch(backend=backend) as batch:                      # lote
    sampler = Sampler(mode=batch)
    job = sampler.run([isa_circuit])
    another_job = sampler.run([another_isa_circuit])""",
                    id="c",
                    setup=SAMPLER_SETUP,
                    size=22,
                )
            ],
            [
                A("hl", "c", at="ejemplos", lines=[1]),
                A("hl", "c", at="multi", lines=[2]),
                A("hl", "c", at="par", lines=[3]),
                A("hl", "c", at="batch", range="4-7"),
            ],
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. Abre el cuaderno de práctica con el comando de abajo; corre con un procesador falso, sin cuenta. [[n1]]Primero mides qué fracción de un GHZ de cinco qubits sale con algún bit cambiado. [[n2]]Después corriges el envío de dos PUBs con distinto número de disparos, que la cero punto cincuenta rechaza. [[n3]]Y por último escribes la función que calcula esa fracción y ves cómo crece con el tamaño del GHZ.
             [[check]]Cada misión tiene una comprobación que se actualiza sola mientras escribes: busca la marca verde.""",
            [
                Mission(
                    "practica/p5-sampler.py",
                    [
                        (
                            1,
                            "Ejecuta un GHZ de 5 qubits y calcula la fracción de disparos con algún bit cambiado.",
                        ),
                        (2, "Reparte dos PUBs con 64 y 128 disparos en dos trabajos."),
                        (
                            3,
                            "Escribe `fraccion_errores(conteos)` y grafícala para GHZ de 2 a 5 qubits.",
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
            [T("Un conteo con ruido también es un resultado.", "subtitle")],
            ask=reflect(
                "Cada qubit más añade una CNOT y una medición. ¿Cuál de las dos crees que aporta más errores? ¿Qué opción de Sampler probarías para averiguarlo?",
                "Tu proyecto usa Estimator, no Sampler. ¿Qué información extra te daría ver los conteos de cada cadena de bits?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Sampler recibe circuitos con mediciones. [[r2]]Devuelve un BitArray por registro, e intervalos de ejecución en la metadata. [[r3]]Los disparos siguen una precedencia, y en la cero punto cincuenta deben coincidir en todo el trabajo.
             [[r4]]Y sus opciones activan cada técnica por separado.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "get-started-with-sampler",
        "sampler-input-output",
        "sampler-options",
        "sampler-examples",
    ],
    practice=[
        "Ejecuta un GHZ de 5 qubits con `Sampler(mode=FakeBelemV2())` y cuenta qué fracción de disparos no es `0…0` ni `1…1`.",
        "Activa `sampler.options.twirling.enable_measure = True` y compara esa fracción.",
    ],
)

# ------------------------------------------------------------------ 5.6 Executor
EXEC = """import numpy as np
from qiskit.circuit import QuantumCircuit, Parameter
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime import Executor
from qiskit_ibm_runtime.quantum_program import QuantumProgram
from qiskit_ibm_runtime.fake_provider import FakeManilaV2
from samplomatic import build
from samplomatic.transpiler import generate_boxing_pass_manager

backend = FakeManilaV2()
circuit = QuantumCircuit(3)
circuit.h(0)
circuit.cx(0, 1)
circuit.cx(1, 2)
circuit.rz(Parameter("theta"), 0)
circuit.rz(Parameter("phi"), 1)
circuit.measure_all()
pm = generate_preset_pass_manager(backend=backend, optimization_level=0)

program = QuantumProgram(shots=1024)
program.append_circuit_item(pm.run(circuit), circuit_arguments=np.random.rand(10, 2))

pm.post_scheduling = generate_boxing_pass_manager(enable_gates=True, enable_measures=True)
template, samplex = build(pm.run(circuit))
program.append_samplex_item(template, samplex=samplex,
                            samplex_arguments={"parameter_values": np.random.rand(10, 2)},
                            shape=(28, 10))

result = Executor(mode=backend).run(program).result()
print(result[0]["meas"].shape)
print(result[1]["meas"].shape, result[1]["measurement_flips.meas"].shape)"""
s_cierre, a_cierre = resumen(
    [
        "`QuantumProgram(shots=…)` con `CircuitItem` y `SamplexItem`",
        "cajas anotadas (`generate_boxing_pass_manager`) → `build()` → plantilla + samplex",
        "forma: ejes extrínsecos (barrido, aleatorizaciones) + intrínsecos (disparos, bits)",
        "resultados: arreglos NumPy · deshacer twirling con XOR de `measurement_flips`",
    ]
)
executor = lesson(
    "p5-executor",
    "Executor",
    "La primitiva de bajo nivel: programas cuánticos, elementos de circuito y de samplex, broadcasting con ejes intrínsecos y extrínsecos, PEC y cómo migrar desde Sampler.",
    [
        "construir un `QuantumProgram` con elementos de circuito y de samplex",
        "predecir la forma de los resultados de Executor",
        "decidir si migrar de Sampler a Executor",
    ],
    [
        beat(
            "intro",
            ("", "Una primitiva sin decisiones implícitas"),
            """Executor muestrea registros de salida, como Sampler, pero sin supresión ni mitigación de errores incorporadas. Forma parte del modelo de ejecución dirigida: tú expresas la intención y Executor la sigue al pie de la letra.
             [[base]]Qiskit todavía no tiene una clase base para Executor. [[samp]]Y para usar samplex necesitas el paquete Samplomatic.""",
            [T("Executor", "title"), Sh("$ pip install samplomatic", id="s", hidden=True)],
            [A("show", "s", at="samp")],
        ),
        beat(
            "programa",
            ("", "El programa cuántico"),
            """La entrada de Executor no es una lista de PUBs, sino un QuantumProgram: una lista de tareas, con un único número de disparos para todo el programa. Si necesitas otro número de disparos, es otro programa, otro trabajo.
             [[circ]]Un CircuitItem es un circuito con sus valores de parámetros, que se ejecuta tal cual, sin aleatorizar. Aquí, diez juegos de dos parámetros.
             [[samp]]Un SamplexItem lleva un circuito plantilla, un samplex que genera parámetros aleatorios en el servidor, por ejemplo para twirling, y los argumentos del samplex.""",
            [Code(EXEC, id="c", size=17)],
            [
                A("hl", "c", at="programa", lines=[20]),
                A("hl", "c", at="circ", lines=[21]),
                A("hl", "c", at="samp", range="23-27"),
            ],
        ),
        beat(
            "cajas",
            ("", "Cajas, plantilla y samplex"),
            """El samplex se construye en dos pasos. [[box]]Primero, generate boxing pass manager agrupa las puertas de dos qubits y las mediciones en cajas, y les añade una anotación de twirling. Aquí lo enganchamos como etapa post scheduling del transpilador.
             [[build]]Luego, build devuelve dos cosas: la plantilla, un circuito equivalente con las puertas de un qubit convertidas en puertas parametrizadas, y el samplex, que sabe generar los parámetros aleatorios.
             [[shape]]Al añadirlo, shape veintiocho por diez pide veintiocho aleatorizaciones para cada uno de los diez juegos de parámetros.""",
            [Code(EXEC, id="c", size=17)],
            [
                A("hl", "c", at="box", lines=[23]),
                A("hl", "c", at="build", lines=[24]),
                A("hl", "c", at="shape", range="25-27"),
            ],
        ),
        beat(
            "pred_resultado",
            ("", "Antes de ver la forma"),
            """El programa ya corrió. Mira lo que pedimos. [[circ]]El CircuitItem lleva diez juegos de dos parámetros. [[shots]]El programa usa mil veinticuatro disparos, [[bits]]y el circuito mide tres bits.
             [[cual]]Apuesta: ¿qué forma tiene el arreglo de la primera tarea, result de cero, meas?""",
            [Code(EXEC, id="c", size=17, norun=True)],
            [
                A("hl", "c", at="circ", lines=[21]),
                A("hl", "c", at="shots", lines=[20]),
                A("hl", "c", at="bits", lines=[17]),
            ],
            ask=predict(
                '¿Qué forma tiene `result[0]["meas"]`?',
                ["`(10, 1024, 3)`", "`(1024, 3)`", "`(10, 3)`", "`(3, 1024, 10)`"],
                "Anotado. Ahora los resultados.",
            ),
        ),
        beat(
            "resultado",
            ("", "Los resultados"),
            """La salida es un QuantumProgramResult, con una entrada por tarea, en el mismo orden. Cada entrada es un diccionario con el nombre del registro como clave y un arreglo NumPy de booleanos como valor.
             [[c0]]Para el CircuitItem: diez juegos de parámetros, mil veinticuatro disparos, tres bits: la respuesta de tu apuesta. [[c1]]Para el SamplexItem: veintiocho aleatorizaciones por diez juegos por mil veinticuatro disparos por tres bits.
             [[flips]]Y measurement flips meas guarda las inversiones de bit que introdujo el twirling de mediciones: una por aleatorización. Se deshacen con un XOR clásico. Executor no corrige nada por ti.""",
            [
                Code(EXEC, id="c", size=17),
                Out(
                    "(10, 1024, 3)\n(28, 10, 1024, 3) (28, 10, 1, 3)",
                    id="o",
                    hidden=True,
                    check=True,
                ),
                Code(
                    'unflipped = result[1]["meas"] ^ result[1]["measurement_flips.meas"]',
                    id="x",
                    hidden=True,
                ),
            ],
            [
                A("hl", "c", at="resultado", range="29-31"),
                A("show", "o", at="c0"),
                A("show", "x", at="flips"),
            ],
        ),
        beat(
            "ejes",
            ("", "Ejes intrínsecos y extrínsecos"),
            """Executor también usa broadcasting, pero distingue dos tipos de ejes. [[intr]]Los intrínsecos, a la derecha, los fija el tipo de dato: para dos parámetros, la forma intrínseca es dos; para un escalar, como un factor de ruido, vacía.
             [[extr]]Los extrínsecos, a la izquierda, son tus barridos. Solo ellos se combinan por broadcasting.
             [[ej]]Parámetros con forma cuatro, uno, dos y factores de ruido con forma tres dan un barrido de cuatro por tres: doce configuraciones. [[shots]]Cada configuración recibe todos los disparos; no se reparten.""",
            [
                Table(
                    ["Entrada", "Forma completa", "Extrínseca", "Intrínseca"],
                    [
                        ["`parameter_values`", "(4, 1, 2)", "(4, 1)", "(2,)"],
                        ["`noise_scale`", "(3,)", "(3,)", "()"],
                        ["**combinado**", "—", "(4, 3)", "—"],
                        ["salida `meas`", "(4, 3, 1024, 4)", "(4, 3)", "(1024, 4) disparos × bits"],
                    ],
                    id="t",
                    stagger=True,
                    size=23,
                )
            ],
            [
                A("item", "t", at="intr", i=0),
                A("item", "t", at="intr", t=2, i=1),
                A("item", "t", at="ej", i=2),
                A("item", "t", at="shots", i=3),
            ],
        ),
        beat(
            "shape",
            ("", "El parámetro shape"),
            """shape añade ejes de aleatorización. [[sin]]Si lo omites, hay una ejecución por configuración: aleatorizada, pero una sola, sin el beneficio de promediar. Ojo: activar twirling no basta, hay que pedir varias aleatorizaciones.
             [[con]]Con forma veinte por diez, veinte aleatorizaciones para cada una de diez configuraciones. [[multi]]Y puedes organizarlas en varios ejes, como dos por catorce por diez.
             [[regla]]La regla: shape debe poder obtenerse por broadcasting de las formas de entrada, alineando por la derecha.""",
            [
                Table(
                    ["Entrada extrínseca", "`shape`", "Resultado"],
                    [
                        ["(10,)", "(10,)", "10 configuraciones · 1 aleatorización"],
                        ["(10,)", "(5, 10)", "10 configuraciones · 5 aleatorizaciones"],
                        ["(10,)", "(2, 3, 10)", "10 · 2×3 = 6 aleatorizaciones"],
                        ["(4, 3)", "(2, 1, 3)", "12 configuraciones · 2 (el 1 se expande a 4)"],
                    ],
                    id="t",
                    stagger=True,
                    size=23,
                )
            ],
            [
                A("item", "t", at="sin", i=0),
                A("item", "t", at="con", i=1),
                A("item", "t", at="multi", i=2),
                A("item", "t", at="regla", i=3),
            ],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Predice la forma.""",
            [
                T(
                    "`parameter_values` con forma (10, 2) (dos parámetros), `shape=(2, 14, 10)`, 1024 disparos y un registro de 4 bits.",
                    "body",
                )
            ],
            ask=choice(
                '¿Qué forma tiene `result[0]["meas"]`?',
                ["(10, 1024, 4)", "(28, 10, 1024, 4)", "(2, 14, 10, 1024, 4)", "(2, 14, 10, 2)"],
                2,
                "Correcto: los ejes extrínsecos (2, 14, 10) más los intrínsecos de salida (1024 disparos, 4 bits).",
                wrong=[
                    "Faltan los ejes de aleatorización.",
                    "La forma (2, 14) no se aplana: se conserva.",
                    None,
                    "Los intrínsecos de la salida son disparos y bits, no parámetros.",
                ],
            ),
        ),
        beat(
            "pec",
            ("", "Ejemplo: PEC con Executor"),
            """El ejemplo avanzado de la guía hace cancelación probabilística de errores, PEC, sobre un circuito espejo de diez qubits: el circuito seguido de su inverso, que idealmente devuelve todo a cero.
             [[cajas]]Se crean dos versiones con cajas: una solo con twirling, otra además con inyección de ruido. [[aprender]]NoiseLearnerV3 aprende el ruido de las tres cajas distintas. [[run]]Executor ejecuta novecientas aleatorizaciones de cada versión, con factores de ruido menos uno para PEC.
             [[res]]Resultado: con solo twirling, los valores esperados de Z rondan cero coma siete; con PEC, cero coma noventa y ocho. El valor ideal es uno.""",
            [
                Flow(
                    [
                        dict(t="Circuito espejo", s="10 qubits"),
                        dict(t="Cajas", s="Twirl · InjectNoise"),
                        dict(t="NoiseLearnerV3", s="3 cajas únicas"),
                        dict(t="Executor", s="900 aleatorizaciones · escala −1"),
                    ],
                    id="f",
                    stagger=True,
                ),
                Hist(
                    [["twirling", 0.68], ["PEC", 0.975], ["ideal", 1]],
                    id="h",
                    hidden=True,
                    h=130,
                    ymax=1.15,
                    digits=2,
                    color="teal",
                ),
            ],
            [
                A("item", "f", at="pec", i=0),
                A("item", "f", at="cajas", i=1),
                A("item", "f", at="aprender", i=2),
                A("item", "f", at="run", i=3),
                A("show", "h", at="res"),
                A("grow", "h", at="res"),
            ],
        ),
        beat(
            "migrar",
            ("", "¿Migrar de Sampler a Executor?"),
            """¿Deberías migrar? [[si]]Sí, si eres una científica o científico que hace experimentos a escala de utilidad y necesita control fino y reproducible del twirling, del aprendizaje e inyección de ruido o de los cambios de base; o si necesitas algo que solo ofrece Executor.
             [[no]]No, si quieres una interfaz simple que gestione los errores por ti. [[lim]]Además, Executor está en beta, y la guía de migración cubre Sampler, no Estimator.
             [[mapa]]La correspondencia: PUBs pasan a ser elementos del programa; las opciones de twirling, cajas anotadas y samplex; los disparos, un único valor en el programa; y los BitArray, arreglos NumPy, con el twirling de medición deshecho a mano.""",
            [
                Table(
                    ["Concepto", "Sampler", "Executor"],
                    [
                        ["Entrada", "lista de PUBs", "`QuantumProgram`"],
                        [
                            "Parámetros",
                            "`(circ, params, shots)`",
                            "`append_circuit_item(circ, circuit_arguments=…)`",
                        ],
                        [
                            "Twirling",
                            "`options.twirling`",
                            "cajas anotadas + `append_samplex_item`",
                        ],
                        ["Disparos", "por PUB o `run`", "`QuantumProgram(shots=…)`"],
                        [
                            "Datos",
                            "`result[0].data.meas` (`BitArray`)",
                            '`result[0]["meas"]` (`np.ndarray`)',
                        ],
                        [
                            "Twirling de medición",
                            "se deshace solo",
                            "XOR con `measurement_flips.meas`",
                        ],
                    ],
                    id="t",
                    stagger=True,
                    size=20,
                )
            ],
            [
                A("item", "t", at="mapa", i=0),
                A("item", "t", at="mapa", t=1, i=1),
                A("item", "t", at="mapa", t=2, i=2),
                A("item", "t", at="mapa", t=3, i=3),
                A("item", "t", at="mapa", t=4, i=4),
                A("item", "t", at="mapa", t=5, i=5),
            ],
        ),
        beat(
            "opciones",
            ("", "Opciones de Executor"),
            """Executor tiene muy pocas opciones, porque casi toda la intención vive en el samplex. [[grupos]]Solo tres grupos: environment, con el nivel de registro o las etiquetas; execution, con init qubits o rep delay; y experimental.
             [[prog]]Lo que cambia la forma de los resultados, como los disparos o meas level, se fija en el QuantumProgram, no en las opciones. [[both]]Desde la cero punto cuarenta y ocho, meas level igual a both pide a la vez mediciones clasificadas y analógicas.""",
            [
                Code(
                    """from qiskit_ibm_runtime.options_models import ExecutorOptions

options = ExecutorOptions(environment={"log_level": "INFO"}, execution={"init_qubits": True})
executor = Executor(mode=backend, options=options)
program = QuantumProgram(shots=1024, meas_level="both")""",
                    id="c",
                    size=22,
                )
            ],
            [A("hl", "c", at="grupos", range="3-4"), A("hl", "c", at="prog", lines=[5])],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Sobre la migración.""",
            [
                T(
                    'Ejecutas Executor con un `SamplexItem` con twirling de mediciones y calculas los conteos directamente de `result[0]["meas"]`.',
                    "body",
                )
            ],
            ask=choice(
                "¿Qué falla?",
                [
                    "nada",
                    "faltó deshacer las inversiones con XOR de `measurement_flips.meas`",
                    "Executor no admite twirling de mediciones",
                ],
                1,
                "Correcto: Executor devuelve las mediciones tal como salieron, con los bits invertidos por el twirling; tú aplicas la corrección.",
                wrong=[
                    "Los bits aleatoriamente invertidos arruinan los conteos.",
                    None,
                    "Sí lo admite, mediante anotaciones.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. Abre el cuaderno de práctica con el comando de abajo; corre con un procesador falso de cinco qubits, sin cuenta. [[n1]]Primero ejecutas un CircuitItem y lees la forma de sus resultados. [[n2]]Después pasas de dos a veinte aleatorizaciones con el parámetro shape. [[n3]]Y por último escribes la función que deshace el twirling de las mediciones con un XOR, y compruebas que el GHZ vuelve a dar solo cero cero cero y uno uno uno.
             [[check]]Cada misión tiene una comprobación que se actualiza sola mientras escribes: busca la marca verde.""",
            [
                Mission(
                    "practica/p5-executor.py",
                    [
                        (1, 'Ejecuta un `CircuitItem` y lee la forma de `result[0]["meas"]`.'),
                        (
                            2,
                            "Cambia `shape` de `(2, 10)` a `(20, 10)` y comprueba la forma de salida.",
                        ),
                        (
                            3,
                            "Escribe `deshacer(item)` con un XOR y mide la fracción de disparos en `000` o `111`.",
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
            [T("Executor no decide por ti: todo lo que corrige, lo corriges tú.", "subtitle")],
            ask=reflect(
                "Sampler deshace el twirling de mediciones por ti y Executor no. ¿Qué ganas a cambio de esa tarea extra?",
                "¿Tu proyecto Ising del hito V necesita Executor, o le basta con Estimator? Justifica con lo que necesitas controlar.",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]Un QuantumProgram reúne elementos de circuito y de samplex. [[r2]]El samplex sale de cajas anotadas y de build. [[r3]]Las formas combinan ejes extrínsecos e intrínsecos.
             [[r4]]Y los resultados son arreglos NumPy que tú posprocesas, incluido deshacer el twirling.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "get-started-with-executor",
        "executor-input-output",
        "executor-broadcasting",
        "executor-options",
        "executor-examples",
        "migrate-from-sampler-to-executor",
    ],
    practice=[
        "Ejecuta el programa de la lección en local y calcula, tras el XOR, la fracción de disparos en `000` o `111`.",
        "Usa `samplex.sample(...)` para generar 3 aleatorizaciones y comprobar con `Operator` que son equivalentes al circuito original.",
    ],
)

# ------------------------------------------------------------------ 5.7 REST
# Context of the parameterized-circuits fragment: the backend name and a transpiler for its ISA.
REST_SETUP = """import qiskit.qasm3
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez

backend = "ibm_fez"
pm = generate_preset_pass_manager(backend=FakeFez(), optimization_level=1)"""
s_cierre, a_cierre = resumen(
    [
        "clave API → token portador IAM (dura ≤ 1 hora)",
        "cabeceras: `Authorization: Bearer …` y `Service-CRN`",
        "`POST /v1/jobs` con `program_id` (`estimator`/`sampler`), `backend`, `params.pubs` en OpenQASM 3",
        "sesiones: `POST /v1/sessions` (`dedicated` o `batch`) · `session_id` en cada trabajo",
    ]
)
rest = lesson(
    "p5-rest",
    "La API REST",
    "Usar IBM Quantum desde cualquier lenguaje: autenticación con tokens portadores, enviar trabajos de Estimator y Sampler con OpenQASM 3, opciones, resultados y sesiones.",
    [
        "obtener un token portador a partir de la clave API",
        "enviar trabajos de Estimator y Sampler por HTTP",
        "crear y cerrar sesiones y lotes con la API",
    ],
    [
        beat(
            "idea",
            ("", "Sin Python"),
            """Todo lo que hace Qiskit con el servicio de IBM pasa por una API REST. Puedes usarla directamente, desde cualquier lenguaje o entorno. Los ejemplos de la guía usan el módulo requests de Python, pero valdría curl o JavaScript.
             [[token]]Primer paso: convertir tu clave API en un token portador del servicio de identidad de IBM Cloud, IAM. Es una credencial temporal: dura como máximo una hora.""",
            [
                Sh(
                    """$ curl -X POST 'https://iam.cloud.ibm.com/identity/token' \\
    -H 'Content-Type: application/x-www-form-urlencoded' \\
    -d 'grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=MI_CLAVE' """,
                    id="c",
                    hidden=True,
                ),
                Code(
                    """{"access_token": "eyJhbGciOiJIUz…", "token_type": "Bearer", "expires_in": 3600}""",
                    "out",
                    id="o",
                    hidden=True,
                ),
            ],
            [A("show", "c", at="token"), A("show", "o", at="token", t=3)],
        ),
        beat(
            "auth",
            ("", "Autenticar las peticiones"),
            """Cada petición lleva dos cabeceras: Authorization, con Bearer y el token, y Service CRN, con el CRN de tu instancia.
             [[env]]En un entorno de confianza, guarda la clave en una variable de entorno, IQP API TOKEN, y léela con os punto environ; aun así, queda en texto plano en tu equipo, así que protégela.
             [[usage]]Por ejemplo, una petición GET a la ruta usage devuelve tu consumo.""",
            [
                Code(
                    """import os
import requests

api_key = os.environ["IQP_API_TOKEN"]
bearer = requests.post("https://iam.cloud.ibm.com/identity/token",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data=f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={api_key}",
).json()["access_token"]
headers = {"Authorization": f"Bearer {bearer}", "Service-CRN": "<CRN>",
           "Content-Type": "application/json"}
usage = requests.get("https://quantum.cloud.ibm.com/api/v1/usage", headers=headers)""",
                    id="c",
                    norun=True,
                    size=21,
                )
            ],
            [
                A("hl", "c", at="auth", range="9-10"),
                A("hl", "c", at="env", lines=[4]),
                A("hl", "c", at="usage", lines=[11]),
            ],
        ),
        beat(
            "estimator",
            ("", "Un trabajo de Estimator"),
            """Para enviar un trabajo, POST a la ruta jobs. El cuerpo lleva el program id, estimator o sampler, el nombre del backend, y en params, los PUBs.
             [[pub]]Cada PUB es una lista: el circuito como texto OpenQASM tres, ya transpilado; los observables, como un diccionario de cadena de Pauli a coeficiente; y los parámetros, o None.
             [[opts]]Las opciones van en params punto options, con los mismos nombres que en Qiskit: resilience con ZNE, dynamical decoupling o twirling.
             [[id]]La respuesta trae el id del trabajo.""",
            [
                Code(
                    """job_input = {
    "program_id": "estimator",
    "backend": "ibm_fez",
    "params": {
        "pubs": [[isa_qasm3, {"IIZII": 1, "XIZZZ": 2.3}, None]],
        "options": {"resilience": {"measure_mitigation": True,
                                   "zne_mitigation": True,
                                   "zne": {"noise_factors": [1, 3, 5]}}},
    },
}
response = requests.post("https://quantum.cloud.ibm.com/api/v1/jobs",
                         headers=headers, json=job_input)
job_id = response.json()["id"]""",
                    id="c",
                    norun=True,
                    size=21,
                )
            ],
            [
                A("hl", "c", at="estimator", range="2-3"),
                A("hl", "c", at="pub", lines=[5]),
                A("hl", "c", at="opts", range="6-8"),
                A("hl", "c", at="id", range="11-13"),
            ],
        ),
        beat(
            "pred_resultados",
            ("", "Antes de leer los resultados"),
            """El trabajo de Sampler terminó, y pedimos sus resultados con un GET. [[ruta]]La respuesta es un JSON con los datos del registro c. [[cual]]Apuesta: ¿cómo viene cada disparo dentro de samples?""",
            [
                Code(
                    """results = requests.get(f"{url}/{job_id}/results", headers=headers).json()["results"]
samples = results[0]["data"]["c"]["samples"]""",
                    id="c",
                    norun=True,
                    size=24,
                )
            ],
            [A("hl", "c", at="ruta", lines=[1])],
            ask=predict(
                "Un disparo medido como `10` en el registro `c` aparece como…",
                [
                    "la cadena `'10'`",
                    "el hexadecimal `'0x2'`",
                    "la lista `[1, 0]`",
                    "el entero `10`",
                ],
                "Anotado. Veamos qué devuelve el servicio.",
            ),
        ),
        beat(
            "resultados",
            ("", "Estado y resultados"),
            """Con el id, GET a jobs barra id da el estado, [[res]]y GET a jobs barra id barra results, los resultados en JSON.
             [[est]]Para Estimator: evs, stds y ensemble standard error, más la metadata. [[sam]]Para Sampler, los datos del registro c vienen como samples: cada disparo es un número hexadecimal, y esa es la respuesta de tu apuesta. Cero x tres es uno uno en binario.""",
            [
                Code(
                    """state = requests.get(f"{url}/{job_id}", headers=headers).json()["state"]
results = requests.get(f"{url}/{job_id}/results", headers=headers).json()["results"]""",
                    id="c",
                    norun=True,
                ),
                Code(
                    """Estimator: [{'data': {'evs': 0.7429, 'stds': 0.0299, 'ensemble_standard_error': 0.0326}, …}]
Sampler:   results[0]['data']['c']['samples'] → ['0x3', '0x0', '0x2', '0x1', …]""",
                    "out",
                    id="o",
                    hidden=True,
                ),
            ],
            [A("hl", "c", at="res", lines=[2]), A("show", "o", at="est")],
        ),
        beat(
            "q1",
            ("", "Comprueba"),
            """Lee un resultado de Sampler por REST.""",
            [Code("['0x3', '0x0', '0x2', '0x1']", "out")],
            ask=choice(
                "¿Qué cadena de bits es `'0x2'` en un registro de 2 bits?",
                ["`'01'`", "`'10'`", "`'11'`"],
                1,
                "Correcto: 2 en binario es `10`: el bit 1 vale 1 y el bit 0 vale 0.",
                wrong=["Ese sería 0x1.", None, "Ese sería 0x3."],
            ),
        ),
        beat(
            "param",
            ("", "Circuitos con parámetros"),
            """Con parámetros, el flujo es: construir y transpilar el circuito en Qiskit, [[qasm]]exportarlo con qasm3 punto dumps, donde los parámetros quedan como entradas, [[vals]]y pasar los valores en el PUB, como lista o como diccionario de nombre a valor, con el número de disparos al final.""",
            [
                Code(
                    """theta, phi = Parameter("theta"), Parameter("phi")
qc = QuantumCircuit(2)
qc.rx(theta, 0)
qc.ry(phi, 1)
qc.cx(0, 1)
qc.measure_all()
qasm_str = qiskit.qasm3.dumps(pm.run(qc))
job_input = {"program_id": "sampler", "backend": backend,
             "params": {"pubs": [[qasm_str, {"theta": 1.57, "phi": 3.14}, 500]]}}""",
                    id="c",
                    setup=REST_SETUP,
                    size=22,
                )
            ],
            [A("hl", "c", at="qasm", lines=[7]), A("hl", "c", at="vals", range="8-9")],
        ),
        beat(
            "sesiones",
            ("", "Sesiones y lotes por REST"),
            """Para las sesiones hay otra ruta, sessions. [[crear]]Un POST con el backend y mode dedicated crea una sesión y devuelve su id. Recuerda: el plan Open no permite sesiones.
             [[usar]]Cada trabajo que quieras dentro de ella lleva ese session id en su cuerpo. [[cerrar]]Al terminar, ciérrala con DELETE en sessions barra id barra close: así reduces la espera de otros usuarios.
             [[batch]]Un lote se crea igual, con mode batch.""",
            [
                Code(
                    """r = requests.post(f"{base}/sessions", headers=headers,
                  json={"backend": backend, "mode": "dedicated"})    # o "batch"
session_id = r.json()["id"]
job_input["session_id"] = session_id
requests.post(f"{base}/jobs", headers=headers, json=job_input)
requests.delete(f"{base}/sessions/{session_id}/close", headers=headers)""",
                    id="c",
                    norun=True,
                    size=22,
                )
            ],
            [
                A("hl", "c", at="crear", range="1-3"),
                A("hl", "c", at="usar", range="4-5"),
                A("hl", "c", at="cerrar", lines=[6]),
                A("hl", "c", at="batch", lines=[2]),
            ],
        ),
        beat(
            "q2",
            ("", "Comprueba"),
            """Sobre la autenticación.""",
            [
                T(
                    "Tu script REST funcionó por la mañana y por la tarde todas las peticiones dan 401.",
                    "body",
                )
            ],
            ask=choice(
                "¿Qué es lo más probable?",
                [
                    "te revocaron la clave API",
                    "el token portador caducó (dura como máximo una hora)",
                    "el CRN cambió",
                ],
                1,
                "Correcto: genera un token portador nuevo a partir de tu clave API.",
                wrong=[
                    "Posible, pero lo habitual es que caduque el token portador.",
                    None,
                    "El CRN de una instancia no cambia.",
                ],
            ),
        ),
        beat(
            "mision",
            ("", "Tu turno"),
            """Ahora te toca a ti. Abre el cuaderno de práctica con el comando de abajo; prepara los cuerpos de los trabajos y lee resultados, todo en tu equipo, sin enviar nada. [[n1]]Primero armas el cuerpo de un trabajo de Sampler con un circuito en OpenQASM tres. [[n2]]Después corriges la lectura de los disparos en hexadecimal para que los conteos coincidan con get counts. [[n3]]Y por último escribes la función que arma el cuerpo de un trabajo de Estimator, con su observable y sus opciones.
             [[check]]Cada misión tiene una comprobación que se actualiza sola mientras escribes: busca la marca verde.""",
            [
                Mission(
                    "practica/p5-rest.py",
                    [
                        (
                            1,
                            "Arma el cuerpo JSON de un trabajo de Sampler con el circuito en OpenQASM 3.",
                        ),
                        (
                            2,
                            "Corrige la decodificación de `samples` para que los conteos coincidan con `get_counts()`.",
                        ),
                        (
                            3,
                            "Escribe `cuerpo_estimator(isa, observable, opciones)` y comprueba que es JSON válido.",
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
            ("", "Tu proyecto: hito V"),
            """Y con esto llegas al hito cinco del proyecto: tu primera ejecución en un procesador cuántico real, con un presupuesto de como máximo un minuto de QPU.
             [[estimar]]Antes de enviar, estimas el tiempo de QPU con una fórmula que el propio cuaderno te explica. [[falso]]El cuaderno corre completo en un procesador falso, sin cuenta, y sus comprobaciones pasan ahí. [[real]]Un interruptor, bien marcado, manda el mismo trabajo a hardware real con tu cuenta guardada, y solo se envía si pulsas el botón y la estimación cabe en el presupuesto.""",
            [
                M(r"M(t)=\frac1N\sum_i\langle Z_i\rangle", size=46),
                Mission(
                    "practica/proyecto/hito5.py",
                    [
                        (
                            1,
                            "Recalcula la referencia: Hamiltoniano, pasos de Trotter y magnetización exacta.",
                        ),
                        (2, "Estima el uso de QPU antes de enviar y comprueba que cabe en 60 s."),
                        (
                            3,
                            "Ejecuta con `Estimator` sin mitigación; el interruptor ⚠️ lo envía a un QPU real.",
                        ),
                    ],
                    title="Proyecto Ising · Hito V",
                    id="m",
                    hidden=True,
                ),
            ],
            [A("show", "m", at="estimar")],
        ),
        beat(
            "reflexion",
            ("", "Reflexiona"),
            """Dos preguntas para cerrar la parte.""",
            [T("Antes de pagar por una ejecución, haz las cuentas.", "subtitle")],
            ask=reflect(
                "Tu estimación de uso para el hito V dio varios segundos. ¿Qué cambiarías, y en qué orden, si superara tu presupuesto de un minuto?",
                "Cuando tengas la curva medida en un QPU, ¿qué parte de la diferencia con la curva exacta atribuirías al error de Trotter y qué parte al ruido? ¿Cómo lo comprobarías?",
            ),
        ),
        beat(
            "cierre",
            ("", "Resumen"),
            """Resumen. [[r1]]La clave API se cambia por un token portador de una hora. [[r2]]Cada petición lleva Authorization y Service CRN. [[r3]]Los trabajos se envían a jobs con program id, backend y PUBs en OpenQASM tres.
             [[r4]]Y las sesiones y lotes se crean en sessions. Con esto termina la Parte cinco.""",
            s_cierre,
            a_cierre,
        ),
    ],
    sources=[
        "cloud-setup-rest-api",
        "estimator-rest-api",
        "sampler-rest-api",
        "execution-modes-rest-api",
    ],
    practice=[
        "Escribe un script con `requests` que liste tus trabajos recientes (consulta la [referencia de la API REST](https://quantum.cloud.ibm.com/docs/en/api/qiskit-runtime-rest)).",
        "Exporta a OpenQASM 3 un circuito transpilado para un backend y envíalo como trabajo de Sampler por REST.",
    ],
)

LESSONS = [cuenta, hola, opciones, estimator, sampler, executor, rest]
