"""The learner path and the optional reference guides of the Qiskit course."""

from typing import Any

PARTS: list[dict[str, Any]] = [
    dict(
        n=1,
        title="Unidad 1 · Tu primer circuito",
        desc="Construye, mide y lee un circuito de Bell; después prepara el primer paso del proyecto Ising.",
        lessons=[
            ("p1-quickstart", "Tu primer circuito: el estado de Bell", ["quick-start"]),
            ("p2-circuitos", "Construir circuitos", ["construct-circuits"]),
            ("p2-medir", "Medir qubits", ["measure-qubits"]),
            ("p2-orden-bits", "El orden de los bits", ["bit-ordering"]),
            ("p1-cierre", "Repaso: de Bell a Ising", []),
        ],
    ),
    dict(
        n=2,
        title="Unidad 2 · Operadores y observables",
        desc="Pasa de circuitos a operadores, observables y gráficos para interpretar lo que calculas.",
        lessons=[
            ("p1-patrones", "El flujo de trabajo: patrones de Qiskit", ["intro-to-patterns"]),
            (
                "p2-operadores",
                "Operadores: Operator, Pauli y SparsePauliOp",
                ["operators-overview", "operator-class"],
            ),
            (
                "p2-observables",
                "Observables en la base de Pauli y síntesis de unitarios",
                ["specify-observables-pauli", "synthesize-unitary-operators"],
            ),
            ("p2-biblioteca", "La biblioteca de circuitos", ["circuit-library"]),
            (
                "p2-visualizar",
                "Visualizar circuitos, estados y resultados",
                [
                    "visualize-circuits",
                    "plot-quantum-states",
                    "visualize-results",
                    "visualize-circuit-timing",
                ],
            ),
            ("p2-cierre", "Repaso: medir la cadena", []),
        ],
    ),
    dict(
        n=3,
        title="Unidad 3 · Simular",
        desc="Usa las primitivas y los simuladores para comparar una evolución exacta con sus aproximaciones.",
        lessons=[
            (
                "p4-primitivas",
                "Las primitivas: Sampler y Estimator",
                ["primitives", "get-started-with-backend-primitives"],
            ),
            ("p4-pubs", "Entradas y salidas: PUBs y broadcasting", ["primitive-input-output"]),
            (
                "p4-simular-exacto",
                "Simulación exacta con las primitivas del SDK",
                ["simulate-with-qiskit-sdk-primitives", "debugging-tools"],
            ),
            (
                "p4-estabilizadores",
                "Simular circuitos de Clifford",
                ["simulate-stabilizer-circuits"],
            ),
            ("p4-cierre", "Repaso: cuándo fiarte de una simulación", []),
        ],
    ),
    dict(
        n=4,
        title="Unidad 4 · Transpilar",
        desc="Convierte el circuito abstracto en uno que respeta las puertas y la conectividad del procesador.",
        lessons=[
            ("p3-transpilar", "Por qué hay que transpilar", ["transpile"]),
            ("p3-etapas", "Las seis etapas del transpilador", ["transpiler-stages"]),
            (
                "p3-niveles",
                "Niveles de optimización y parámetros",
                [
                    "set-optimization",
                    "common-parameters",
                    "defaults-and-configuration-options",
                    "circuit-transpilation-settings",
                ],
            ),
            (
                "p3-target",
                "Representar un computador cuántico: Target",
                ["represent-quantum-computers", "custom-backend"],
            ),
            (
                "p3-pass-managers",
                "Pass managers y desacoplamiento dinámico",
                ["transpile-with-pass-managers", "dynamical-decoupling-pass-manager"],
            ),
            (
                "p3-pases-propios",
                "Escribir pases propios: el DAG",
                ["custom-transpiler-pass", "DAG-representation"],
            ),
            (
                "p3-plugins",
                "Plugins y transpilación con IA",
                ["transpiler-plugins", "create-transpiler-plugin", "ai-transpiler-passes"],
            ),
            ("p3-cierre", "Repaso: presupuesto de profundidad", []),
        ],
    ),
    dict(
        n=5,
        title="Unidad 5 · Ruido",
        desc="Mide el ruido, prueba modelos locales y aplica supresión y mitigación antes de volver al hardware.",
        lessons=[
            (
                "p4-aer-ruido",
                "Qiskit Aer y modelos de ruido",
                ["simulate-with-qiskit-aer", "build-noise-models"],
            ),
            (
                "p4-local-testing",
                "Modo de prueba local y backends falsos",
                ["local-testing-mode", "local-simulators"],
            ),
            ("p6-panorama", "Panorama de la gestión del ruido", ["error-mitigation-overview"]),
            ("p6-supresion", "Supresión: desacoplamiento dinámico y twirling", []),
            (
                "p6-mitigacion",
                "Mitigación: TREX, ZNE, PEA, PEC y PNA",
                ["error-mitigation-and-suppression-techniques"],
            ),
            (
                "p6-configurar",
                "Configurar el ruido en Estimator y Sampler",
                ["estimator-noise-management", "sampler-noise-management"],
            ),
            (
                "p6-aprender-ruido",
                "Aprender el ruido",
                ["noise-learning", "migrate-to-noise-learner-v3"],
            ),
            ("p6-postseleccion", "Postselección", ["post-selection"]),
            ("p6-neat", "Depurar trabajos con NEAT", ["debug-qiskit-runtime-jobs"]),
        ],
    ),
    dict(
        n=6,
        title="Unidad 6 · Al hardware",
        desc="Lleva el experimento a IBM Quantum, controla la ejecución y organiza trabajos reales.",
        lessons=[
            ("p5-hello-world", "Hola mundo en un QPU", ["hello-world"]),
            (
                "p5-opciones",
                "Primitivas de IBM y sus opciones",
                [
                    "qiskit-runtime-primitives",
                    "runtime-options-overview",
                    "directed-execution-model",
                ],
            ),
            (
                "p5-estimator",
                "Estimator en IBM Quantum",
                [
                    "get-started-with-estimator",
                    "estimator-input-output",
                    "estimator-options",
                    "estimator-examples",
                ],
            ),
            (
                "p5-sampler",
                "Sampler en IBM Quantum",
                [
                    "get-started-with-sampler",
                    "sampler-input-output",
                    "sampler-options",
                    "sampler-examples",
                ],
            ),
            (
                "p5-executor",
                "Executor",
                [
                    "get-started-with-executor",
                    "executor-input-output",
                    "executor-broadcasting",
                    "executor-options",
                    "executor-examples",
                    "migrate-from-sampler-to-executor",
                ],
            ),
            (
                "p2-control-clasico",
                "Control clásico, feedforward y stretch",
                ["classical-feedforward-and-control-flow", "stretch"],
            ),
            ("p7-dinamicos", "Circuitos dinámicos en hardware", ["execute-dynamic-circuits"]),
            ("p7-fraccionales", "Puertas fraccionales", ["fractional-gates", "pulse-migration"]),
            ("p7-temporizacion", "Temporización de circuitos", ["qiskit-runtime-circuit-timing"]),
            (
                "p7-modos",
                "Modos de ejecución: job, batch y session",
                [
                    "execution-modes",
                    "choose-execution-mode",
                    "run-jobs-batch",
                    "run-jobs-session",
                    "execution-modes-faq",
                ],
            ),
            (
                "p7-trabajos",
                "Monitorear, etiquetar y guardar trabajos",
                ["monitor-job", "add-job-tags", "save-jobs"],
            ),
        ],
    ),
    dict(
        n=7,
        title="Unidad 7 · Escalar",
        desc="Empaqueta el trabajo y usa Serverless, addons y Functions para llevarlo más lejos.",
        lessons=[
            (
                "p8-serverless",
                "Qiskit Serverless",
                [
                    "serverless",
                    "serverless-first-program",
                    "serverless-run-first-workload",
                    "serverless-manage-resources",
                    "serverless-port-code",
                ],
            ),
            ("p8-addons", "Qiskit addons", ["addons"]),
            ("p8-functions", "Qiskit Functions", ["functions", "functions-get-started"]),
            (
                "p8-circuit-functions",
                "Funciones de circuito",
                [
                    "algorithmiq-tem",
                    "q-ctrl-performance-management",
                    "qedma-qesem",
                    "quantum-elements-orbit",
                ],
            ),
            (
                "p8-app-functions",
                "Funciones de aplicación",
                [
                    "kipu-optimization",
                    "multiverse-computing-singularity",
                    "q-ctrl-optimization-solver",
                    "global-data-quantum-optimizer",
                    "colibritd-pde",
                    "qunova-chemistry",
                    "aqarios-constrained-quantum-optimizer",
                    "parity-twine-optimizer",
                ],
            ),
            (
                "p8-plantillas",
                "Plantillas de Qiskit Functions",
                [
                    "qiskit-function-templates",
                    "function-template-chemistry-workflow",
                    "function-template-hamiltonian-simulation",
                    "function-template-aqc-trotter",
                ],
            ),
        ],
    ),
]


GUIDES: list[tuple[str, str, list[str]]] = [
    ("p1-que-es-qiskit", "Qué es Qiskit", ["index", "tools-intro", "compute-services"]),
    (
        "p1-instalar",
        "Instalar y configurar Qiskit",
        [
            "install-qiskit",
            "install-qiskit-source",
            "configure-qiskit-local",
            "online-lab-environments",
            "install-qiskit-runtime",
            "install-qiskit-runtime-source",
        ],
    ),
    ("p1-composer", "IBM Quantum Composer", ["composer"]),
    (
        "p2-qasm",
        "OpenQASM y guardar circuitos",
        [
            "introduction-to-qasm",
            "interoperate-qiskit-qasm2",
            "interoperate-qiskit-qasm3",
            "qasm-feature-table",
            "save-circuits",
        ],
    ),
    (
        "p5-cuenta",
        "Cuenta de IBM Cloud, planes y credenciales",
        [
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
    ),
    (
        "p5-rest",
        "La API REST",
        [
            "cloud-setup-rest-api",
            "estimator-rest-api",
            "sampler-rest-api",
            "execution-modes-rest-api",
        ],
    ),
    (
        "p7-procesadores",
        "Los procesadores de IBM",
        [
            "processor-types",
            "qpu-information",
            "calibration-jobs",
            "repetition-rate-execution",
            "retired-qpus",
        ],
    ),
    (
        "p7-colas-costos",
        "Colas, tiempos y costos",
        [
            "fair-share-scheduler",
            "view-cost",
            "estimate-job-run-time",
            "minimize-time",
            "max-execution-time",
            "job-limits",
        ],
    ),
    (
        "p9-proveedores",
        "Integrar recursos cuánticos externos",
        ["create-a-provider", "qiskit-backendv1-to-v2"],
    ),
    ("p9-c-api", "La API de C de Qiskit", ["install-c-api", "c-extension-for-python"]),
    ("p9-hpc", "HPC: QRMI y Slurm", ["qrmi", "slurm-plugin", "slurm-hpc-ux"]),
    (
        "p9-ia",
        "IA para programar con Qiskit",
        ["qiskit-code-assistant", "qiskit-mcp-servers", "ai-skills"],
    ),
    (
        "p9-migraciones",
        "Versiones y migraciones",
        [
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
    ),
    (
        "p10-organizaciones",
        "Organizaciones e instancias",
        [
            "considerations-set-up-runtime",
            "quickstart-steps-org",
            "instances",
            "allocation-limits",
            "access-instances-platform-apis",
            "logging",
        ],
    ),
    (
        "p10-acceso",
        "Cuentas, grupos de acceso y usuarios",
        [
            "cloud-account-structure",
            "access-groups",
            "custom-roles",
            "invite-and-manage-users",
            "manage-appid",
            "manage-cloud-users",
        ],
    ),
    (
        "p10-seguridad",
        "Seguridad y cumplimiento",
        [
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
    ),
    (
        "p10-comunidad",
        "Soporte, preguntas frecuentes y código abierto",
        ["support", "faq", "open-source", "code-of-conduct"],
    ),
]
