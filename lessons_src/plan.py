"""Full map of the course: parts, lessons and the original guides each one covers.

Each guide in .cache/qiskit-docs/docs/guides/_toc.json must appear in exactly one lesson
(build.py checks it), and each lesson in this plan must have its parte*.py module.
The titles and descriptions are course text, so they are in Spanish.
"""

from typing import Any

PARTS: list[dict[str, Any]] = [
    dict(
        n=1,
        title="Parte I · Primeros pasos",
        desc="Qué es Qiskit, el flujo de trabajo de cuatro pasos, cómo instalarlo y tu primer circuito.",
        lessons=[
            ("p1-que-es-qiskit", "Qué es Qiskit", ["index", "tools-intro", "compute-services"]),
            ("p1-patrones", "El flujo de trabajo: patrones de Qiskit", ["intro-to-patterns"]),
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
            ("p1-quickstart", "Tu primer circuito: el estado de Bell", ["quick-start"]),
            ("p1-composer", "IBM Quantum Composer", ["composer"]),
            ("p1-cierre", "Cierre de la Parte I: repaso y un paso de Trotter", []),
        ],
    ),
    dict(
        n=2,
        title="Parte II · Circuitos y operadores",
        desc="QuantumCircuit a fondo: registros, composición, medición, orden de bits, la biblioteca de circuitos, operadores y OpenQASM.",
        lessons=[
            ("p2-circuitos", "Construir circuitos", ["construct-circuits"]),
            ("p2-medir", "Medir qubits", ["measure-qubits"]),
            ("p2-orden-bits", "El orden de los bits", ["bit-ordering"]),
            ("p2-biblioteca", "La biblioteca de circuitos", ["circuit-library"]),
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
            (
                "p2-control-clasico",
                "Control clásico, feedforward y stretch",
                ["classical-feedforward-and-control-flow", "stretch"],
            ),
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
                "p2-visualizar",
                "Visualizar circuitos, estados y resultados",
                [
                    "visualize-circuits",
                    "plot-quantum-states",
                    "visualize-results",
                    "visualize-circuit-timing",
                ],
            ),
            ("p2-cierre", "Cierre de la Parte II: repaso y magnetización", []),
        ],
    ),
    dict(
        n=3,
        title="Parte III · Transpilación",
        desc="Cómo un circuito abstracto se convierte en uno que el hardware puede ejecutar, y cómo controlar ese proceso.",
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
            ("p3-cierre", "Cierre de la Parte III: repaso y cuántos pasos caben", []),
        ],
    ),
    dict(
        n=4,
        title="Parte IV · Primitivas y simulación",
        desc="Sampler y Estimator, sus entradas (PUBs) y salidas, y cómo simular con y sin ruido antes de usar hardware.",
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
                "p4-aer-ruido",
                "Qiskit Aer y modelos de ruido",
                ["simulate-with-qiskit-aer", "build-noise-models"],
            ),
            (
                "p4-estabilizadores",
                "Simular circuitos de Clifford",
                ["simulate-stabilizer-circuits"],
            ),
            (
                "p4-local-testing",
                "Modo de prueba local y backends falsos",
                ["local-testing-mode", "local-simulators"],
            ),
            ("p4-cierre", "Cierre de la Parte IV: repaso y tiempo de validez", []),
        ],
    ),
    dict(
        n=5,
        title="Parte V · Ejecutar en IBM Quantum",
        desc="Cuenta, credenciales, el primer programa en hardware real y las primitivas Estimator, Sampler y Executor de IBM.",
        lessons=[
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
                "p5-rest",
                "La API REST",
                [
                    "cloud-setup-rest-api",
                    "estimator-rest-api",
                    "sampler-rest-api",
                    "execution-modes-rest-api",
                ],
            ),
        ],
    ),
    dict(
        n=6,
        title="Parte VI · Ruido: supresión y mitigación",
        desc="De dónde vienen los errores y qué técnicas ofrece IBM para suprimirlos y mitigarlos.",
        lessons=[
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
        n=7,
        title="Parte VII · Ejecución avanzada y gestión de trabajos",
        desc="Circuitos dinámicos, puertas fraccionales, los procesadores de IBM, colas, costos y modos de ejecución.",
        lessons=[
            ("p7-dinamicos", "Circuitos dinámicos en hardware", ["execute-dynamic-circuits"]),
            ("p7-fraccionales", "Puertas fraccionales", ["fractional-gates", "pulse-migration"]),
            ("p7-temporizacion", "Temporización de circuitos", ["qiskit-runtime-circuit-timing"]),
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
                "p7-trabajos",
                "Monitorear, etiquetar y guardar trabajos",
                ["monitor-job", "add-job-tags", "save-jobs"],
            ),
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
        ],
    ),
    dict(
        n=8,
        title="Parte VIII · Serverless, addons y Qiskit Functions",
        desc="Ejecutar flujos completos en la nube, las herramientas de investigación (addons) y el catálogo de funciones.",
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
    dict(
        n=9,
        title="Parte IX · Extender e integrar Qiskit",
        desc="Proveedores propios, la API de C, computación de alto rendimiento, herramientas de IA y cómo migrar entre versiones.",
        lessons=[
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
        ],
    ),
    dict(
        n=10,
        title="Parte X · Organizaciones, seguridad y comunidad",
        desc="Administrar instancias, usuarios y permisos; seguridad y cumplimiento; soporte y código abierto.",
        lessons=[
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
        ],
    ),
]
