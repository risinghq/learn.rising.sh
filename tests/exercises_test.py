"""Tests for the exercise format, the grader and what build.py publishes.

    uv run pytest tests/exercises_test.py

Each exercise in exercises/ is graded with its solution (it passes) and with a
wrong solution (it fails with a useful message). The tests need no network.
"""

import ast
import collections
import contextlib
import functools
import importlib.util
import io
import json
import os
import re
import resource
import subprocess
import sys
import tempfile
import textwrap
import types
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "lessons_src"), str(ROOT / "runner")]
os.environ.setdefault("MPLBACKEND", "Agg")

import build  # noqa: E402
import sizing  # noqa: E402

from qgcheck import grade, learner, spec  # noqa: E402
from qgcheck.runner import TIMEOUT, job_env  # noqa: E402


def load_tool(name: str, filename: str) -> types.ModuleType:
    tool = importlib.util.spec_from_file_location(name, ROOT / "tools" / filename)
    assert tool and tool.loader
    module = importlib.util.module_from_spec(tool)
    tool.loader.exec_module(module)
    return module


exercises_tool = load_tool("exercises_tool", "exercises.py")

REAL = spec.all_ids()

GHZ_WITHOUT_CHAIN = """
from qiskit import QuantumCircuit
def ghz(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    return qc
"""

GHZ_WITHOUT_MEASURE = """
from qiskit import QuantumCircuit
def ghz(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    for k in range(n - 1):
        qc.cx(k, k + 1)
    return qc
"""


LEAPFROG_EULER = """
def leapfrog(x, v, dt, pasos):
    for _ in range(pasos):
        x, v = x + dt * v, v - dt * x
    return x, v
"""

LEAPFROG_KICK_THEN_DRIFT = """
def leapfrog(x, v, dt, pasos):
    for _ in range(pasos):
        v -= dt * x
        x += dt * v
    return x, v
"""

EULER_WITH_THE_NEW_X = """
def euler(x, v, dt, pasos):
    for _ in range(pasos):
        x += dt * v
        v -= dt * x
    return x, v
"""

BELL_CNOT_REVERSED = """
from qiskit import QuantumCircuit
bell = QuantumCircuit(2)
bell.h(0)
bell.cx(1, 0)
bell.measure_all()
"""

PREPARAR_MOST_SIGNIFICANT_FIRST = """
from qiskit import QuantumCircuit
def preparar(k, n):
    qc = QuantumCircuit(n)
    for qubit, bit in enumerate(format(k, f"0{n}b")):
        if bit == "1":
            qc.x(qubit)
    return qc
"""

PERIODO_SMALL_ANGLE = """
import math
def periodo(theta0, dt=0.001):
    return 2 * math.pi
"""

ORBITA_EULER = """
def orbita(x, y, vx, vy, dt, pasos):
    for _ in range(pasos):
        r3 = (x * x + y * y) ** 1.5
        x, y, vx, vy = x + dt * vx, y + dt * vy, vx - dt * x / r3, vy - dt * y / r3
    return x, y, vx, vy
"""

ORBITA_KICK_THEN_DRIFT = """
def orbita(x, y, vx, vy, dt, pasos):
    for _ in range(pasos):
        r3 = (x * x + y * y) ** 1.5
        vx -= dt * x / r3
        vy -= dt * y / r3
        x += dt * vx
        y += dt * vy
    return x, y, vx, vy
"""


def broken(exercise_id: str, old: str, new: str) -> str:
    """Return the reference solution with an incorrect change."""
    code = (spec.folder(exercise_id) / "solution.py").read_text(encoding="utf-8")
    assert old in code, (exercise_id, old)
    return code.replace(old, new)


def mutant(exercise_id: str, name: str) -> str:
    """Return the wrong code in `tests/mutants/<exercise>/<name>.py`.

    Each file is a whole program, not a change to solution.py, so rewriting the
    reference solution does not break the tests.
    """
    return (ROOT / "tests" / "mutants" / exercise_id / f"{name}.py").read_text(encoding="utf-8")


def mutants_of(exercise_id: str) -> list[tuple[str, str]]:
    folder = ROOT / "tests" / "mutants" / exercise_id
    return [(exercise_id, path.read_text(encoding="utf-8")) for path in sorted(folder.glob("*.py"))]


# (exercise, wrong code, text expected in some failure message)
WRONG = [
    (
        "p1-quickstart/bell-distinto",
        "from qiskit import QuantumCircuit\nanti = QuantumCircuit(2)\nanti.h(0)\nanti.cx(0, 1)\nanti.z(1)\nanti.measure_all()\n",
        "Salen ['00', '11']",
    ),
    ("p1-quickstart/ghz", GHZ_WITHOUT_CHAIN, "Con n = 3 salen ['000', '011']"),
    ("p1-quickstart/ghz", GHZ_WITHOUT_MEASURE, "falta `measure_all()`"),
    ("f1-euler-leapfrog/leapfrog", LEAPFROG_EULER, "pasos = 10, `leapfrog` devuelve"),
    ("f1-pendulo/periodo", PERIODO_SMALL_ANGLE, "theta0 = 3.0, `periodo` devuelve 6.28"),
    ("f1-euler-leapfrog/euler-roto", EULER_WITH_THE_NEW_X, "pasos = 100, `euler` devuelve"),
    ("f1-pendulo/periodo-roto", PERIODO_SMALL_ANGLE, "theta0 = 3.0, `periodo` devuelve 6.28"),
    ("p1-quickstart/bell-roto", BELL_CNOT_REVERSED, "Salen ['00', '01']"),
    (
        "p2-orden-bits/preparar-roto",
        PREPARAR_MOST_SIGNIFICANT_FIRST,
        "Con k = 5 y n = 4 la amplitud está en el índice 10",
    ),
    ("f1-kepler/orbita", ORBITA_EULER, "pasos = 1000, `orbita` devuelve"),
    (
        "p2-control-clasico/siempre-uno",
        textwrap.dedent("""
        from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
        q, c = QuantumRegister(1, "q"), ClassicalRegister(1, "c")
        siempre_uno = QuantumCircuit(q, c)
        siempre_uno.h(q[0])
        siempre_uno.measure(q[0], c[0])
        siempre_uno.x(q[0])
        siempre_uno.measure(q[0], c[0])
     """),
        "Salen {",
    ),
    (
        "p2-control-clasico/hasta-uno",
        textwrap.dedent("""
        from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
        def hasta_uno():
            q, c = QuantumRegister(1, "q"), ClassicalRegister(1, "c")
            qc = QuantumCircuit(q, c)
            qc.h(q[0])
            qc.measure(q[0], c[0])
            with qc.while_loop((c, 0)):
                qc.x(q[0])
                qc.measure(q[0], c[0])
            return qc
     """),
        "no de una puerta X",
    ),
    *[
        (eid, broken(eid, old, new), expected)
        for eid, old, new, expected in [
            (
                "p2-biblioteca/nlocal-barato",
                ', entanglement="linear"',
                "",
                "Ahora tiene 6 puertas de dos qubits",
            ),
            (
                "p2-biblioteca/parametros-nlocal",
                "prediccion = 12",
                "prediccion = 9",
                "una más que las repeticiones",
            ),
            ("p2-biblioteca/sumar", "    qc.initialize(y, b)\n", "", "`sumar(5, 6)` mide"),
            (
                "p2-circuitos/familia-theta",
                "np.linspace(0, np.pi, 21)",
                "np.linspace(0, np.pi, 11)",
                "Hay 11 circuitos y deben ser 21",
            ),
            (
                "p2-circuitos/ghz-menos-profundo",
                "ghz6.cx(1, 5)",
                "ghz6.cx(0, 5)",
                "La profundidad es 5",
            ),
            ("p2-circuitos/profundidad", "prediccion = 3", "prediccion = 5", "cuenta las capas"),
            (
                "p2-medir/bell-1-3",
                "remove_final_measurements(inplace=False)",
                "copy()",
                "no debe tener bits clásicos",
            ),
            (
                "p2-medir/bits-clasicos",
                "prediccion = 4",
                "prediccion = 3",
                "no reutiliza el registro",
            ),
            (
                "p2-medir/qubit-al-bit",
                "measure([2, 0], [0, 1])",
                "measure([0, 2], [0, 1])",
                "Ahora salen ['10']",
            ),
            ("p2-observables/magnetizacion", "1 / n", "1", "M_Z vale 4.00"),
            ("p2-observables/medir-y", "qc.sdg(0)\n    ", "", "Sin el cambio de base"),
            (
                "p2-observables/terminos-ising",
                "prediccion = 7",
                "prediccion = 8",
                "pares de vecinos",
            ),
            ("p2-operadores/compose-qargs", "qargs=[2, 1]", "qargs=[1, 2]", "Todavía no es `ZXI`"),
            ("p2-operadores/heisenberg", '"ZZ"', '"XX"', "Con n = 2 los autovalores son"),
            (
                "p2-operadores/orden-compose",
                'orden = "ZX"',
                'orden = "XZ"',
                "de derecha a izquierda",
            ),
            (
                "p2-orden-bits/cadena-de-bits",
                'prediccion = "101"',
                'prediccion = "011"',
                "bit del qubit 2",
            ),
            (
                "p2-orden-bits/preparar",
                "(k >> j) & 1",
                "(k >> (n - 1 - j)) & 1",
                "la amplitud está en el índice 10",
            ),
            ("p2-orden-bits/preparar-011", "x([0, 1])", "x([1, 2])", "Ahora el estado es ['110']"),
            (
                "p2-qasm/instrucciones-qasm",
                "prediccion = 4",
                "prediccion = 3",
                "son dos instrucciones",
            ),
            (
                "p2-qasm/qasm-antiguo",
                "custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS",
                "strict=True",
                "Todavía no se importa",
            ),
            (
                "p2-qasm/qpy",
                "qpy.load(io.BytesIO(datos))[0]",
                "qpy.load(io.BytesIO(datos))",
                "`qpy.load` devuelve una lista",
            ),
            (
                "p2-visualizar/barras-esperados",
                "ejes.bar(etiquetas, valores_esperados(circuito, etiquetas))",
                "pass",
                "deberían llamarse como las etiquetas",
            ),
            (
                "p2-visualizar/dibujo-texto",
                "plot_barriers=False",
                "plot_barriers=True",
                "Todavía se ven las barreras",
            ),
            (
                "p2-visualizar/probabilidad-00",
                "prediccion = 0.5",
                "prediccion = 0.25",
                "Tu apuesta está lejos",
            ),
            (
                "p2-control-clasico/corregir-moneda",
                'prediccion = "0"',
                'prediccion = "azar"',
                "Sigue las dos ramas",
            ),
            (
                "p2-cierre/curva-trotter",
                "range(K + 1)",
                "range(K)",
                "Con n = 4 y K = 20, `curva_trotter` devuelve 20 valores",
            ),
            (
                "p1-cierre/paso-trotter",
                "rzz(2 * J * dt",
                "rzz(J * dt",
                "Los ángulos de tu circuito son [0.1, 0.1, 0.1]",
            ),
            (
                "p3-cierre/pasos-maximos",
                "d <= presupuesto",
                "d < presupuesto",
                "`pasos_max` devuelve",
            ),
            (
                "p4-cierre/tiempo-de-validez",
                "abs(med - ref) > tol",
                "abs(med - ref) >= tol",
                "`tiempo_de_validez` devuelve 1",
            ),
        ]
    ],
]


def read(exercise_id: str, name: str) -> str:
    return (spec.folder(exercise_id) / name).read_text(encoding="utf-8")


def failed(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [t for t in result["tests"] if not t["passed"]]


QPY_ON_DISK = (
    "    with open(f'{__import__(\"uuid\").uuid4().hex}.qpy', 'wb') as archivo:\n"
    "        qpy.dump(circuito, archivo)\n"
    "        nombre = archivo.name\n"
    "    return open(nombre, 'rb').read()"
)

# Part 3: (exercise, file name in tests/mutants/<exercise>/, text expected in some message).
WRONG += [
    (eid, mutant(eid, name), expected)
    for eid, name, expected in [
        ("p3-transpilar/cz-por-nivel", "operador-roto", "ya no implementa el mismo operador"),
        (
            "p3-transpilar/pass-manager-completo",
            "sin-backend",
            "quedan instrucciones que FakeFez no ejecuta",
        ),
        ("p3-transpilar/es-isa", "acepta-todo", "acepta un circuito con `h` y `ccx`"),
        ("p3-etapas/cx-ghz-linea", "suma-uno", "Con n = 8 y nivel = 0 tu función devuelve"),
        ("p3-etapas/layout-estrella", "layout-identidad", "el routing inserta 1 swap"),
        ("p3-etapas/mejor-de-semillas", "otro-circuito", "Con otro circuito"),
        ("p3-niveles/ecr-por-nivel", "cuenta-cx", "el nivel 3 debería usar menos ecr"),
        ("p3-niveles/aproximar", "exacto", "salen 3 ecr"),
        ("p3-niveles/fidelidad", "nivel-fijo", "Con el estado marcado 2 y nivel = 0"),
        ("p3-target/mi-backend", "par-extra", "`MiBackend` admite cz en los pares"),
        ("p3-target/anillo-averiado", "par-averiado-barato", "usa los pares [(1, 2)]"),
        ("p3-target/cadena-n", "par-cierra-anillo", "`cz` queda en los pares"),
        ("p3-pass-managers/traducir-iones", "sin-base", "Quedan las puertas"),
        ("p3-pass-managers/cancelar-pares", "solo-h", "Con pares = «S, S†» salen"),
        ("p3-pass-managers/dd-pm", "qubit-4", "Había 0 x"),
        (
            "p3-pases-propios/dag-operaciones",
            "ultimos-qubits",
            "la Toffoli del resultado actúa en los qubits",
        ),
        ("p3-pases-propios/swap-a-cx", "sustituye-cx", "el circuito cambia"),
        (
            "p3-pases-propios/contar-dos-qubits",
            "sin-clave-si-cero",
            "Sin puertas de dos qubits escribe n2q",
        ),
        ("p3-plugins/listar-metodos", "unitaria-vacia", "`unitaria_metodos` vale []"),
        ("p3-plugins/routing-method", "basic", "Con metodo = 'basic' salen"),
        ("p3-plugins/clifford-plugin", "solo-tres", "el resultado queda intacto"),
    ]
]

# Part 5: (exercise, file name in tests/mutants/<exercise>/, text expected in some message).
WRONG += [
    (eid, mutant(eid, name), expected)
    for eid, name, expected in [
        ("p5-cuenta/guardar-cuenta", "sin-predeterminada", "las cuentas predeterminadas son []"),
        (
            "p5-cuenta/cuenta-predeterminada",
            "pisa-personal",
            "quedan guardadas las cuentas ['clase']",
        ),
        ("p5-cuenta/minutos-libres", "tope-fijo", "Con tope = 20 y hoy = 11 devuelve 5"),
        (
            "p5-cuenta/minutos-libres",
            "cuenta-futuro",
            "Con un uso en el día 40 y hoy = 10 devuelve 3",
        ),
        ("p5-hello-world/bell-seis-observables", "todo-uno", "En `valores`, IZ vale 1.0"),
        ("p5-hello-world/mas-disparos", "demasiados", "Con `disparos` = 100000"),
        ("p5-hello-world/correlaciones-ghz", "etiquetas-al-reves", "Con n = 5 las etiquetas son"),
        (
            "p5-opciones/cuatro-formas",
            "cambia-disparos",
            "En `por_update`, `default_shots` vale 1000",
        ),
        (
            "p5-opciones/copia-de-opciones",
            "copia-sin-efecto",
            "Un trabajo de `est` ejecuta 100 disparos",
        ),
        ("p5-opciones/crear-estimator", "sin-disparos", "`default_shots` vale None"),
        ("p5-estimator/barrido", "un-observable", "`evs` tiene forma (1, 100)"),
        ("p5-estimator/precision", "demasiada-precision", "`error_zz` vale 0.0022"),
        ("p5-estimator/valor-s", "signos-rotos", "Con `evs_chsh`, |S| llega a 0.25"),
        ("p5-sampler/ghz5-ruido", "sin-ideales", "`fraccion_ruido` vale 1.0"),
        (
            "p5-sampler/trabajos-por-disparos",
            "cambia-el-defecto",
            "`sampler.run([isa])` usa 128 disparos",
        ),
        (
            "p5-sampler/fraccion-errores",
            "cuenta-sin-dividir",
            "Con conteos = {'01': 3, '10': 2} devuelve 5",
        ),
        ("p5-sampler/fraccion-errores", "sin-calcular", "`error_2` vale 0.0"),
        ("p5-executor/circuit-item", "una-configuracion", "`argumentos` tiene forma (1, 2)"),
        (
            "p5-executor/aleatorizaciones",
            "menos-configuraciones",
            "`forma_twirl` vale (20, 5, 256, 3)",
        ),
        ("p5-executor/deshacer", "sin-corregir", "Con `item`, la fracción de disparos 000 o 111"),
        ("p5-rest/cuerpo-sampler", "lista-vacia", "`parametros` se envía como []"),
        ("p5-rest/decodificar-samples", "ancho-fijo", "n_bits = 4 devuelve {'00': 1, '101': 2}"),
        (
            "p5-rest/cuerpo-estimator",
            "sin-layout",
            "Con observable = ZZ y XX el PUB lleva el observable {'ZZ': 0.5, 'XX': -1.0}",
        ),
    ]
]

WRONG += [
    (eid, mutant(eid, name), expected)
    for eid, name, expected in [
        ("p6-panorama/bell-ruidoso", "otro-ruido", "`cuentas_bell` tiene 1000 disparos"),
        ("p6-panorama/mas-ruido-cx", "fraccion-a-mano", "`frac_mas` vale 0.3 y"),
        ("p6-panorama/mas-ruido-cx", "p-cx-enorme", "`p_cx` vale 0.9"),
        (
            "p6-panorama/distancia-tv",
            "sin-la-mitad",
            "Con a = {'00': 3, '11': 1} y b = {'00': 1, '11': 1} devuelve 0.5",
        ),
        (
            "p6-panorama/distancia-tv",
            "solo-cadenas-de-a",
            "Con a = {'00': 6, '11': 2, '01': 2} y b = {'00': 5, '10': 5} devuelve 0.25",
        ),
        (
            "p6-panorama/distancia-tv",
            "total-de-a",
            "y al intercambiar a y b devuelve 1.25",
        ),
        (
            "p6-supresion/rellenar-con-xx",
            "cuatro-x",
            "`con_xx` añade 4 pulsos X",
        ),
        (
            "p6-supresion/rellenar-con-xx",
            "x-de-mas",
            "`con_xx` se parece a `isa` en 0.0",
        ),
        (
            "p6-supresion/cuatro-pulsos",
            "valor-a-mano",
            "`pulsos_secuencia` vale 4 pero `con_secuencia` añade 2 pulsos X",
        ),
        (
            "p6-supresion/cuatro-pulsos",
            "x-de-mas",
            "`con_secuencia` se parece a `isa` en 0.0",
        ),
        (
            "p6-supresion/variante-twirling",
            "ignora-la-etiqueta",
            "Con antes = 'IX' lo que va antes de la CX se parece a esa Pauli en 0.0",
        ),
        ("p6-mitigacion/zne-lineal", "otro-ruido", "`valores` es [0.51, 0.13, 0.04]"),
        (
            "p6-mitigacion/zne-exponencial",
            "sin-ordenada",
            "Con factores = [1, 3, 5, 7] y valores = [0.7459, 0.6485, 0.5638, 0.4901] devuelve 1.0.",
        ),
        (
            "p6-mitigacion/zne-exponencial",
            "factores-fijos",
            "Con factores = [1, 2] y valores = [0.9, 0.81] devuelve 0.9487",
        ),
        ("p6-mitigacion/pesos-pec", "lam-fijo", "Con lam = 0.01 devuelve a = 1.0394736842105263"),
        (
            "p6-configurar/opciones-por-defecto",
            "nivel-2",
            "`estimator` tiene el nivel 2",
        ),
        (
            "p6-configurar/trex-y-zne",
            "nivel-por-defecto",
            "`opciones.resilience_level` vale 1",
        ),
        ("p6-configurar/trex-y-zne", "opciones-aparte", "Las opciones de `estimator` quedan"),
        (
            "p6-configurar/preparar",
            "sampler-acepta",
            "Con primitiva = 'sampler' y tecnicas = {'trex'} devuelve {'dd': False, 'twirling': None}",
        ),
        (
            "p6-configurar/preparar",
            "dd-siempre",
            "Con primitiva = 'estimator' y tecnicas = set() queda",
        ),
        ("p6-aprender-ruido/costo-de-invertir", "otras-tasas", "Las tasas de `modelo` son [0.02"),
        ("p6-aprender-ruido/amplificar", "solo-triple", "Con factor = 1 las tasas quedan"),
        (
            "p6-aprender-ruido/amplificar",
            "cambia-el-original",
            "Tras amplificar con factor = 3, las tasas de `modelo` son",
        ),
        (
            "p6-aprender-ruido/aprender-fidelidad",
            "dos-puntos",
            "Con ds = [1, 2, 3, 6] y valores = [0.95, 0.9, 0.84, 0.6] devuelve f = 0.94737",
        ),
        ("p6-neat/capas-y-ruido", "modelo-propio", "`dif_backend` vale [4.15, 6.45, 11.04]"),
        ("p6-neat/modelo-propio", "dif-a-mano", "`dif_propio` vale [7.54, 10.37, 13.2]"),
        ("p6-neat/modelo-propio", "p-cx-enorme", "`p_cx` vale 0.9"),
        ("p6-neat/sugerencia", "limites-incluidos", "Con dif = 90 devuelve ['PEA']"),
        ("p6-neat/sugerencia", "redondea", "Con dif = 79.9 devuelve ['PEA']"),
        ("p7-dinamicos/correccion-dinamica", "condicion-invertida", "`correccion()` devuelve"),
        ("p7-dinamicos/registro-un-if", "dos-if", "Con bits = 3"),
        ("p7-dinamicos/valida-limites", "acepta-todo", "registro-grande"),
        ("p7-fraccionales/compara-cadena", "sin-rzz", "Con n = 4 y pasos = 2"),
        ("p7-fraccionales/angulo-especial", "ignora-angulo", "theta_zz"),
        ("p7-fraccionales/cadena-ising", "sin-capas", "Con n = 6 y pasos = 3"),
        ("p7-temporizacion/leer-lineas", "sin-conversion", "Con texto ="),
        ("p7-temporizacion/fin-en-nanosegundos", "sin-duracion", "Con registros ="),
        ("p7-temporizacion/programa-isa", "vacio", "Con n = 1"),
        ("p7-procesadores/razon-medicion", "sin-familia", "Con backend ="),
        ("p7-procesadores/mejor-t1", "indice-fijo", "Con backend ="),
        ("p7-procesadores/mejor-cadena", "primeros-qubits", "Con k = 5"),
        ("p7-colas-costos/uso-bell", "sin-costo", "Con disparos = 8192"),
        ("p7-colas-costos/ejecuciones-pub", "solo-shots", "Con shape = (2, 3)"),
        ("p7-colas-costos/estimar-uso", "sin-ejecuciones", "Con qubits = 5"),
        ("p7-trabajos/guardar-leer", "sin-conteos", "Con seed = 8"),
        ("p7-trabajos/anadir-etiqueta", "pierde-anteriores", "Con etiquetas = ['a', 'b']"),
        ("p7-trabajos/guardar-por-etiqueta", "no-guarda", "Con etiquetas = ['b']"),
        ("p7-modos/tres-trabajos", "vacio", "Con n_trabajos = 2"),
        ("p7-modos/partir-circuitos", "un-grupo", "Con circuitos ="),
        ("p7-modos/elegir-modo", "no-juntar", "Con argumentos ="),
    ]
]

# Part 4: (exercise, text of solution.py, its replacement, text expected in some message).
WRONG += [
    (eid, broken(eid, old, new), expected)
    for eid, old, new, expected in [
        (
            "p4-primitivas/dos-vistas",
            "prediccion = [1, 0, 1]",
            "prediccion = [1, 1, 1]",
            "Tu apuesta no coincide con lo que calcula Estimator",
        ),
        (
            "p4-primitivas/backend-sampler",
            'sampler = BackendSamplerV2(backend=backend, options={"seed_simulator": 3})',
            "sampler = StatevectorSampler(seed=1)",
            "`sampler` es un StatevectorSampler",
        ),
        ("p4-primitivas/z-desde-conteos", ") / total", ") / 1", "`z_desde_conteos` devuelve"),
        (
            "p4-pubs/formas",
            "prediccion = ((5,), (4, 6))",
            "prediccion = ((5,), (4, 1))",
            "Tu apuesta no coincide con las formas",
        ),
        (
            "p4-pubs/observables-3x10",
            '[[SparsePauliOp(p)] for p in ["ZZZ", "XXX", "YYY"]]',
            'SparsePauliOp(["ZZZ", "XXX", "YYY"])',
            "tiene la forma (10,)",
        ),
        (
            "p4-pubs/probabilidad-uno",
            "return (1 - datos",
            "return (1 + datos",
            "`probabilidad_uno` devuelve",
        ),
        (
            "p4-simular-exacto/valores-exactos",
            "prediccion = [4, 2 + 3 ** 0.5, 2]",
            "prediccion = [4, 4, 4]",
            "Tu apuesta no coincide con lo que calcula Estimator",
        ),
        ("p4-simular-exacto/precision", "precision = 0.005", "precision = 0.5", "Baja `precision`"),
        (
            "p4-simular-exacto/cuatro-pubs",
            "    pubs = [(qubit, None, n) for n in disparos]\n"
            "    resultado = sampler.run(pubs).result()\n",
            "    resultado = [sampler.run([(qubit, None, n)]).result()[0] for n in disparos]\n",
            "llama a `run` 3 veces",
        ),
        (
            "p4-aer-ruido/ideal-vs-ruidoso",
            "prediccion = 0.93",
            "prediccion = 0.5",
            "Tu apuesta está lejos",
        ),
        ("p4-aer-ruido/p-a-la-mitad", "p = 0.13", "p = 0.02", "Sube `p`"),
        (
            "p4-aer-ruido/error-de-lectura",
            "[[1 - p01, p01], [p10, 1 - p10]]",
            "[[1 - p10, p10], [p01, 1 - p01]]",
            "Preparando |1⟩ lees 0",
        ),
        (
            "p4-estabilizadores/ghz-100",
            "prediccion = 2",
            "prediccion = 100",
            "Tu apuesta no coincide con las cadenas",
        ),
        (
            "p4-estabilizadores/rz-de-clifford",
            "angulo = np.pi / 2",
            "angulo = np.pi / 2 + 0.1",
            "sigue rechazando el circuito",
        ),
        ("p4-estabilizadores/a-clifford", "np.rint(", "np.floor(", "`a_clifford` devuelve"),
        (
            "p4-local-testing/bell-fake",
            "prediccion = 4096",
            "prediccion = 1024",
            "Tu apuesta no coincide con los disparos",
        ),
        (
            "p4-local-testing/sin-ruido",
            "backend = AerSimulator()",
            "backend = FakeManilaV2()",
            "`backend` es un FakeManilaV2",
        ),
        (
            "p4-local-testing/mitigacion",
            "measure_mitigation = mitigar",
            "measure_mitigation = False",
            "el valor mitigado no es mejor",
        ),
    ]
]

WRONG += [
    (eid, mutant(eid, name), expected)
    for eid, name, expected in [
        ("p8-addons/mejor-capas", "absorbe-siempre", "`mejor_k` devuelve"),
        (
            "p8-addons/presupuesto-operador",
            "sin-presupuesto",
            "`terminos_con_presupuesto` devuelve",
        ),
        ("p8-addons/retropropaga-observable", "valor-roto", "`retropropaga` devuelve"),
        ("p8-app-functions/maximo-corte", "sin-cuadraticos", "`maximo_corte` devuelve"),
        (
            "p8-app-functions/penalizacion-cartera",
            "penalizacion-ignorada",
            "`elegir_cartera` devuelve",
        ),
        ("p8-app-functions/qubo-ising", "sin-cuadratico", "`qubo_a_ising` devuelve"),
        ("p8-circuit-functions/barrido-precision", "sin-dispersion", "`dispersiones` devuelve"),
        (
            "p8-circuit-functions/precision-alcanzable",
            "sin-error",
            "devuelve 0.01",
        ),
        (
            "p8-circuit-functions/tiempo-qpu",
            "ignora-volumen",
            "`tiempo_qpu` devuelve",
        ),
        ("p8-functions/backend-accesible", "acepta-todos", "`backend_accesible` devuelve"),
        ("p8-functions/ejecutar-funcion", "valor-roto", "`ejecutar` devuelve"),
        ("p8-functions/resumen-trabajo", "oculta-error", "`resumen` devuelve"),
        ("p8-plantillas/dos-backends", "sin-instante-cero", "`comparar_backends` devuelve"),
        ("p8-plantillas/pasos-en-qpu", "sin-validacion", "devuelve 12"),
        ("p8-plantillas/validar-pronto", "construye-mal", "`mi_funcion` devuelve"),
        ("p8-serverless/ejecutar-programa", "sin-profundidades", "`ejecutar` devuelve"),
        ("p8-serverless/entrada-serializable", "pierde-circuitos", "`argumentos` devuelve"),
        ("p8-serverless/tareas-paralelas", "sin-tareas", "`profundidades` devuelve"),
    ]
]

# Wrong code that fails the hidden cases: (exercise, code). The message of each failing hidden
# case is compared with the reference solution in test_hidden_messages_*.
MUTANTS = [
    ("p1-quickstart/ghz", GHZ_WITHOUT_CHAIN),
    (
        "p1-quickstart/bell-distinto",
        "from qiskit import QuantumCircuit\nanti = QuantumCircuit(2)\nanti.x(0)\nanti.measure_all()\n",
    ),
    ("f1-euler-leapfrog/leapfrog", LEAPFROG_EULER),
    ("f1-euler-leapfrog/leapfrog", LEAPFROG_KICK_THEN_DRIFT),
    ("f1-pendulo/periodo", PERIODO_SMALL_ANGLE),
    ("f1-euler-leapfrog/euler-roto", EULER_WITH_THE_NEW_X),
    ("f1-pendulo/periodo-roto", PERIODO_SMALL_ANGLE),
    ("p1-quickstart/bell-roto", BELL_CNOT_REVERSED),
    ("p2-orden-bits/preparar-roto", PREPARAR_MOST_SIGNIFICANT_FIRST),
    ("f1-kepler/orbita", ORBITA_EULER),
    ("f1-kepler/orbita", ORBITA_KICK_THEN_DRIFT),
    *[
        (eid, broken(eid, old, new))
        for eid, old, new in [
            ("p2-biblioteca/nlocal-barato", '"ry", "cz", reps=1', '"rx", "cz", reps=1'),
            ("p2-biblioteca/parametros-nlocal", 'n_local(3, "rx", "cz")', 'n_local(3, "ry", "cz")'),
            ("p2-biblioteca/sumar", "    qc.initialize(y, b)\n", ""),
            ("p2-biblioteca/sumar", "qc.measure([*b, *cout], res)", "qc.measure(b, res[:4])"),
            ("p2-circuitos/familia-theta", 'print(len(familia), "circuitos")', "base = familia[0]"),
            (
                "p2-circuitos/familia-theta",
                "np.linspace(0, np.pi, 21)",
                "np.linspace(0, np.pi, 22)[:-1]",
            ),
            (
                "p2-circuitos/familia-theta",
                "np.linspace(0, np.pi, 21)",
                "np.linspace(0, np.pi, 11)",
            ),
            ("p2-circuitos/ghz-menos-profundo", "ghz6.cx(1, 5)", "ghz6.ccx(0, 1, 5)"),
            ("p2-circuitos/profundidad", "qc.z(2)", "qc.y(2)"),
            ("p2-control-clasico/corregir-moneda", "if_test((c[0], 1))", "if_test((c[0], 0))"),
            (
                "p2-control-clasico/hasta-uno",
                "    with qc.while_loop((c, 0)):\n        qc.h(q[0])\n        qc.measure(q[0], c[0])\n",
                "",
            ),
            ("p2-control-clasico/siempre-uno", "(c[0], 0)", "(c[0], 1)"),
            (
                "p2-medir/bell-1-3",
                "bell13.remove_final_measurements(inplace=False)",
                "QuantumCircuit(5)",
            ),
            ("p2-medir/bell-1-3", "bell13.cx(1, 3)\n", "bell13.cx(1, 3)\nbell13.x(0)\n"),
            ("p2-medir/bits-clasicos", "qc.x([0, 2])", "qc.x([0, 1])"),
            ("p2-medir/qubit-al-bit", "emparejado.x(2)", "emparejado.x(1)"),
            ("p2-observables/magnetizacion", "1 / n", "1"),
            ("p2-observables/magnetizacion", 'eje="Z"', 'eje="X"'),
            ("p2-observables/magnetizacion", "num_qubits=n)", "num_qubits=max(n, 2))"),
            ("p2-observables/medir-y", "qc = preparacion.copy()", "qc = preparacion"),
            ("p2-observables/medir-y", "    qc.sdg(0)\n", ""),
            ("p2-observables/terminos-ising", '("X", [i], -1)', '("X", [i], 1)'),
            ("p2-operadores/compose-qargs", "qargs=[2, 1]", "qargs=[1, 2]"),
            ("p2-operadores/heisenberg", '"ZZ"', '"XX"'),
            ("p2-operadores/orden-compose", 'B = Operator(Pauli("Z"))', 'B = Operator(Pauli("Y"))'),
            ("p2-orden-bits/cadena-de-bits", "circuito.x([0, 2])", "circuito.x([0, 1])"),
            ("p2-orden-bits/preparar", "(k >> j) & 1", "(k >> (n - 1 - j)) & 1"),
            ("p2-orden-bits/preparar", "QuantumCircuit(n)", "QuantumCircuit(n + 1)"),
            ("p2-orden-bits/preparar", "QuantumCircuit(n)", "QuantumCircuit(n, n)"),
            ("p2-orden-bits/preparar-011", "x([0, 1])", "x([1, 2])"),
            ("p2-qasm/instrucciones-qasm", "h q[0];", "x q[0];"),
            ("p2-qasm/qasm-antiguo", "rxx(0.5)", "rxx(0.7)"),
            (
                "p2-qasm/qasm-antiguo",
                "custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS",
                "strict=True",
            ),
            ("p2-qasm/qpy", "qpy.load(io.BytesIO(datos))[0]", "qpy.load(io.BytesIO(datos))"),
            (
                "p2-qasm/qpy",
                "    archivo = io.BytesIO()\n    qpy.dump(circuito, archivo)\n    return archivo.getvalue()",
                QPY_ON_DISK,
            ),
            (
                "p2-visualizar/barras-esperados",
                "return res.data.evs.flatten()",
                "return res.data.evs.flatten() * 0",
            ),
            ("p2-visualizar/dibujo-texto", "circuito.barrier()\n", ""),
            ("p2-visualizar/probabilidad-00", "estado.crx(pi / 2, 0, 1)", "estado.crx(pi, 0, 1)"),
            ("p2-cierre/curva-trotter", "range(K + 1)", "range(K)"),
            ("p2-cierre/curva-trotter", "trotter(n, J, h, dt, k)", "trotter(n, 1.0, h, dt, k)"),
            ("p1-cierre/paso-trotter", "rzz(2 * J * dt", "rzz(J * dt"),
            ("p1-cierre/paso-trotter", "rx(2 * h * dt, 0)", "rx(h * dt, 0)"),
            ("p3-cierre/pasos-maximos", "d <= presupuesto", "d < presupuesto"),
            ("p3-cierre/pasos-maximos", "range(1, 11)", "range(1, 9)"),
            (
                "p3-cierre/pasos-maximos",
                "generate_preset_pass_manager(3,",
                "generate_preset_pass_manager(0,",
            ),
            ("p4-cierre/tiempo-de-validez", "abs(med - ref) > tol", "abs(med - ref) >= tol"),
            ("p4-cierre/tiempo-de-validez", "abs(med - ref)", "med - ref"),
            ("p4-primitivas/dos-vistas", '"XX"]', '"YY"]'),
            (
                "p4-primitivas/backend-sampler",
                "BackendSamplerV2(backend=backend,",
                "BackendSamplerV2(backend=GenericBackendV2(3, seed=1),",
            ),
            ("p4-primitivas/backend-sampler", "shots=1024", "shots=512"),
            ("p4-primitivas/z-desde-conteos", "cadena[-1 - k]", "cadena[k]"),
            ("p4-primitivas/z-desde-conteos", ") / total", ") / 1"),
            ("p4-pubs/formas", "np.linspace(0, 1, 6)", "np.linspace(0, 1, 7)"),
            ("p4-pubs/observables-3x10", '["ZZZ", "XXX", "YYY"]', '["XXX", "ZZZ", "YYY"]'),
            ("p4-pubs/probabilidad-uno", "return (1 - datos", "return (1 + datos"),
            ("p4-pubs/probabilidad-uno", "[..., None]", "[:, None]"),
            ("p4-pubs/probabilidad-uno", "np.asarray(angulos)", "np.asarray(angulos).squeeze()"),
            ("p4-simular-exacto/valores-exactos", "np.pi / 6", "np.pi / 4"),
            ("p4-simular-exacto/precision", "precision = 0.005", "precision = 0"),
            ("p4-simular-exacto/precision", "precision = 0.005", "precision = 0.5"),
            (
                "p4-simular-exacto/cuatro-pubs",
                "    pubs = [(qubit, None, n) for n in disparos]\n"
                "    resultado = sampler.run(pubs).result()\n",
                "    resultado = [sampler.run([(qubit, None, n)]).result()[0] for n in disparos]\n",
            ),
            (
                "p4-simular-exacto/cuatro-pubs",
                "(qubit, None, n) for n in disparos]",
                "(qubit, None, disparos[0]) for n in disparos]",
            ),
            ("p4-simular-exacto/cuatro-pubs", "return [abs(", "return [-abs("),
            (
                "p4-aer-ruido/ideal-vs-ruidoso",
                "depolarizing_error(0.02, 2)",
                "depolarizing_error(0, 2)",
            ),
            ("p4-aer-ruido/p-a-la-mitad", "p = 0.13", "p = 0.02"),
            (
                "p4-aer-ruido/error-de-lectura",
                "[[1 - p01, p01], [p10, 1 - p10]]",
                "[[1 - p10, p10], [p01, 1 - p01]]",
            ),
            (
                "p4-aer-ruido/error-de-lectura",
                "ruido.add_all_qubit_readout_error(ReadoutError([[1 - p01, p01], [p10, 1 - p10]]))",
                "ruido.add_readout_error(ReadoutError([[1 - p01, p01], [p10, 1 - p10]]), [0])",
            ),
            ("p4-estabilizadores/ghz-100", "ghz100.h(0)\n", ""),
            ("p4-estabilizadores/rz-de-clifford", "angulo = np.pi / 2", "angulo = np.pi / 4"),
            ("p4-estabilizadores/rz-de-clifford", "con_rz.rz(angulo, 0)", "con_rz.rz(np.pi, 0)"),
            ("p4-estabilizadores/rz-de-clifford", "con_rz.h(0)\n", ""),
            ("p4-estabilizadores/a-clifford", "np.rint(", "np.floor("),
            (
                "p4-local-testing/bell-fake",
                "conteos_fake = sampler_fake.run([isa_bell]).result()[0].data.meas.get_counts()",
                'conteos_fake = {"00": 2048, "11": 2048}',
            ),
            (
                "p4-local-testing/sin-ruido",
                "bell_medido.h(0)\n",
                "bell_medido.x(0)\nbell_medido.h(0)\n",
            ),
            ("p4-local-testing/sin-ruido", "run([isa_local])", "run([isa_local], shots=1000)"),
            (
                "p4-local-testing/mitigacion",
                "measure_mitigation = mitigar",
                "measure_mitigation = True",
            ),
            (
                "p4-local-testing/mitigacion",
                ").result()[0].data.evs)",
                ").result()[0].data.evs) + (0.2 if mitigar else 0)",
            ),
        ]
    ],
    *[
        m
        for eid in sorted(e for e in REAL if e.startswith(("p3-", "p5-", "p6-", "p7-", "p8-")))
        for m in mutants_of(eid)
    ],
]


# The `basic` runner instance gives each job 1/4 of a vCPU for TIMEOUT seconds.
# Keep 40% of that budget as margin for host variability.
# This measure assumes the compiled bytecode installed by `mise run install`.
CPU_BUDGET_S = TIMEOUT * float(sizing.TYPES["basic"][0])
CPU_SHARE = 0.6

# Scale the limit by the current slowdown of a fixed reference job under the graded-job environment.
# Hardware instruction counters require `perf_event_paranoid <= 2` or root, unavailable in WSL and CI.
REFERENCE_JOB = """
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
qc = QuantumCircuit(8)
qc.h(0)
for i in range(7):
    qc.cx(i, i + 1)
for i in range(8):
    qc.rz(0.3 * i, i)
for _ in range(20):
    Statevector(qc).probabilities()
a = np.random.default_rng(1).random((300, 300))
for _ in range(5):
    (a @ a).sum()
"""
# CPU seconds for REFERENCE_JOB, run with the environment of a graded job (two BLAS threads), on
# the quiet-host calibration baseline: the smallest of 180 runs on an Intel Core Ultra 7 265K
# with 20 cores. A faster host gets a proportionally tighter limit, while a slower or busier host
# gets a looser limit.
QUIET_REFERENCE_CPU_S = 0.32


def children_cpu() -> float:
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_utime + usage.ru_stime


def slowdown() -> float:
    """How many times slower than idle this host runs the reference job, set up like a graded job."""
    with tempfile.TemporaryDirectory(prefix="qg-ref-") as work:
        before = children_cpu()
        subprocess.run(
            [sys.executable, "-P", "-c", REFERENCE_JOB],
            check=True,
            cwd=work,
            env=job_env(work, os.environ.get("PATH", "")),
            stdin=subprocess.DEVNULL,
        )
        return (children_cpu() - before) / QUIET_REFERENCE_CPU_S


def solution_cpu(exercise_id: str, code: str) -> float:
    before = children_cpu()
    result = grade(exercise_id, code, timeout=60)
    cpu = children_cpu() - before
    assert result["passed"], result
    assert result["tests"] and all(t["passed"] and t["message"] is None for t in result["tests"])
    return cpu


def cpu_limit(slower: float) -> float:
    return CPU_SHARE * CPU_BUDGET_S * slower


@functools.cache
def first_slowdown() -> float:
    return slowdown()


def measure_against_limit(exercise_id: str, code: str) -> tuple[float, float]:
    """The CPU of a solution and the limit it is judged by.

    A quiet host costs one solution run, against the slowdown measured once for the session. A
    solution that goes over that limit is measured again after a fresh calibration, so a loaded
    host judges it by the load of that moment, and the second pair decides.
    """
    cpu = solution_cpu(exercise_id, code)
    limit = cpu_limit(first_slowdown())
    if cpu > limit:
        limit = cpu_limit(slowdown())
        cpu = solution_cpu(exercise_id, code)
    return cpu, limit


@pytest.mark.parametrize("exercise_id", REAL)
def test_solution_passes_within_the_cpu_budget(exercise_id: str) -> None:
    cpu, limit = measure_against_limit(exercise_id, read(exercise_id, "solution.py"))
    assert cpu <= limit, (
        f"The solution used {cpu:.2f} s of CPU; the limit is {limit:.2f} s: {CPU_SHARE:.0%} of "
        f"the {CPU_BUDGET_S} s the runner allows, scaled by how much slower this host runs the "
        "reference job now than when idle."
    )


@pytest.mark.parametrize("exercise_id", REAL)
def test_starter_fails(exercise_id: str) -> None:
    result = grade(exercise_id, read(exercise_id, "starter.py"))
    assert result["error"] is None and not result["passed"] and failed(result)


@pytest.mark.parametrize(
    "exercise_id,code,expected", WRONG, ids=[f"{w[0]}#{k}" for k, w in enumerate(WRONG)]
)
def test_wrong_solution_fails_with_message(exercise_id: str, code: str, expected: str) -> None:
    result = grade(exercise_id, code)
    assert not result["passed"]
    assert any(expected in t["message"] for t in failed(result)), [
        t["message"] for t in failed(result)
    ]


def test_wrong_solutions_cover_every_exercise() -> None:
    assert {w[0] for w in WRONG} == set(REAL)


def learner_names(exercise_id: str) -> set[str]:
    """Names that the starter code defines: the learner's variables and functions."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(read(exercise_id, "starter.py"))):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names |= {t.id for t in node.targets if isinstance(t, ast.Name)}
    return names


def names_its_input(exercise_id: str, message: str) -> bool:
    """A message names its input with `n = 7` or with the learner's name in backticks."""
    return bool(re.search(r"\b\w+ = \S", message)) or any(
        f"`{name}" in message for name in learner_names(exercise_id)
    )


def graded_attempts(exercise_id: str) -> list[str]:
    """The starter code and each wrong code in WRONG for this exercise."""
    return [
        read(exercise_id, "starter.py"),
        *(code for eid, code, *_ in WRONG if eid == exercise_id),
    ]


@pytest.mark.parametrize("exercise_id", REAL)
def test_graded_hidden_messages_name_their_input(exercise_id: str) -> None:
    """What `grade` returns for a failing hidden case says which input it failed on."""
    for code in graded_attempts(exercise_id):
        for test in failed(grade(exercise_id, code)):
            if not test["visible"]:
                assert names_its_input(exercise_id, test["message"]), (
                    f"{test['name']} does not name its input: {test['message']}"
                )


# An `assert` in a case looks at the learner's code through these expressions, and it carries the
# expected values written as literals.
OBSERVED = (
    ast.Name,
    ast.Attribute,
    ast.Subscript,
    ast.Call,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.BoolOp,
    ast.ListComp,
    ast.DictComp,
    ast.List,
    ast.Tuple,
    ast.Dict,
    ast.Set,
)


def plain(value: Any) -> str:
    """repr of a value, with numpy values converted to Python ones, as a message prints them."""
    if isinstance(value, (np.ndarray, np.generic)):
        value = value.tolist()
    return repr(value)


def forms(value: Any) -> list[str]:
    """How a value can appear in a message: its repr and, for a string, the string itself."""
    return [plain(value)] + ([value] if isinstance(value, str) and len(value) > 1 else [])


def informative(value: Any) -> bool:
    """A value a message can show: no modules, functions or objects whose repr is an address."""
    if isinstance(value, (bool, np.bool_, types.ModuleType, type)) or callable(value):
        return False
    return " at 0x" not in repr(value)


def expressions(tree: ast.AST) -> list[ast.expr]:
    """The observable expressions of `tree`. For a literal, the whole collection counts, not each number."""
    found: list[ast.expr] = []
    inside: set[int] = set()
    for node in ast.walk(tree):
        if id(node) in inside:
            continue
        if isinstance(node, (ast.List, ast.Tuple, ast.Dict, ast.Set, ast.UnaryOp)):
            inside |= {id(n) for n in ast.walk(node) if isinstance(n, ast.Constant)}
        number = (
            isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)
        )
        if isinstance(node, ast.expr) and (number or isinstance(node, OBSERVED)):
            found.append(node)
    return found


def names_in(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


class Site:
    """The assert that failed: its expressions and what each one depends on.

    kind[text] is "learner" if the expression depends on the learner's code, "input" if it is an
    input variable of the case (the n of a loop) and "fixed" if it depends on neither: an expected
    value.
    """

    def __init__(self, tree: ast.Module, lineno: int) -> None:
        asserts = [
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.Assert) and n.lineno <= lineno <= (n.end_lineno or n.lineno)
        ]
        node = max(asserts, key=lambda n: n.lineno)
        scope = min(
            (
                n
                for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef)
                and n.lineno <= node.lineno <= (n.end_lineno or n.lineno)
            ),
            key=lambda n: (n.end_lineno or n.lineno) - n.lineno,
        )
        tainted, inputs = self.dependencies(tree, scope)
        self.sources = collections.defaultdict(list)
        for n in ast.walk(scope):
            if isinstance(n, ast.Assign):
                for target in n.targets:
                    for x in ast.walk(target):
                        if isinstance(x, ast.Name):
                            self.sources[x.id].append(n.value)
        self.first = node.lineno
        self.test = {ast.unparse(n): n for n in expressions(node.test)}
        self.message = {ast.unparse(n): n for n in expressions(node.msg)} if node.msg else {}
        self.interpolated = {
            ast.unparse(n.value)
            for n in ast.walk(node.msg or node.test)
            if isinstance(n, ast.FormattedValue)
        }
        self.nodes = [*self.test.values(), *self.message.values()]
        # What the check passes to the learner's code is its input, even if it is a literal or a variable.
        given = [
            a
            for n in ast.walk(scope)
            if isinstance(n, ast.Call) and names_in(n.func) & tainted
            for a in (*n.args, *(k.value for k in n.keywords))
        ]
        given_names = {name for a in given for name in names_in(a)} | inputs
        given_texts = {ast.unparse(a) for a in given}
        self.derived = tainted - {"learner", *(a.arg for a in scope.args.args)}
        self.kind = {}
        for n in self.nodes:
            base = n
            while isinstance(base, (ast.Attribute, ast.Subscript)):
                base = base.value
            if ast.unparse(n) in given_texts or (
                isinstance(base, ast.Name) and base.id in given_names - tainted
            ):
                self.kind[ast.unparse(n)] = "input"
            else:
                self.kind[ast.unparse(n)] = "learner" if names_in(n) & tainted else "fixed"

    def parts(self, node: ast.AST, seen: tuple[str, ...] = ()) -> set[str]:
        """Texts of what the expression takes from the learner's code, also through the variables it uses."""
        found: set[str] = set()
        for n in ast.walk(node):
            if (isinstance(n, ast.Name) and n.id in self.derived) or (
                isinstance(n, (ast.Call, ast.Attribute)) and "learner" in names_in(n)
            ):
                found.add(ast.unparse(n))
            if isinstance(n, ast.Name) and n.id not in seen:
                for source in self.sources[n.id]:
                    found |= self.parts(source, (*seen, n.id))
        return found

    @staticmethod
    def dependencies(tree: ast.Module, scope: ast.FunctionDef) -> tuple[set[str], set[str]]:
        """(names that depend on the learner, input names).

        These depend on the learner: `learner`, the check functions that use it, the parameters and
        what is assigned from them. The variables of a loop over fixed data are input.
        """
        functions = [f for f in tree.body if isinstance(f, ast.FunctionDef)]
        tainted = {"learner", *(a.arg for a in scope.args.args)}
        while True:
            using = {f.name for f in functions if names_in(f) & tainted}
            if using <= tainted:
                break
            tainted |= using
        inputs: set[str] = set()
        changed = True
        while changed:
            changed = False
            for n in ast.walk(scope):
                if isinstance(n, ast.Assign):
                    source, targets = n.value, n.targets
                elif (
                    isinstance(n, (ast.AugAssign, ast.AnnAssign, ast.NamedExpr))
                    and n.value is not None
                ):
                    source, targets = n.value, [n.target]
                elif isinstance(n, (ast.For, ast.comprehension)):
                    source, targets = n.iter, [n.target]
                else:
                    continue
                dependent = bool(names_in(source) & tainted)
                for name in (x.id for t in targets for x in ast.walk(t) if isinstance(x, ast.Name)):
                    if dependent and name not in tainted:
                        tainted.add(name)
                        changed = True
                    elif not dependent and isinstance(n, (ast.For, ast.comprehension)):
                        inputs.add(name)
        return tainted, inputs - tainted


def run_hidden_case(
    exercise_id: str,
    code: str,
    case: str,
    probe: tuple[int, int, list[ast.expr]] | None = None,
) -> tuple[str | None, int | None, collections.Counter[int], dict[str, list[str]]]:
    """Run a hidden case with `code` as the learner's code, in this process.

    Return (message or None, line of the assert that failed, passes through each line, values).
    With probe=(line, times, nodes) it evaluates the nodes on pass number `times` through that
    line, just before its assert, and returns {text of the expression: how a message shows it}.
    """
    check = spec.folder(exercise_id) / "check.py"
    fn = next(fn for fn, shown in spec.load_cases(check) if fn.__name__ == case)
    arrivals: collections.Counter[int] = collections.Counter()
    values: dict[str, list[str]] = {}
    starts: dict[int, int] = {}

    def on_call(frame: types.FrameType, event: str, arg: Any) -> Any:
        if frame.f_code.co_filename != str(check):
            return None

        def on_line(frame: types.FrameType, event: str, arg: Any) -> Any:
            # An assert that spans several lines or uses `and` can return to its first line within
            # the same pass: only the instruction it starts with counts.
            if (
                event == "line"
                and starts.setdefault(frame.f_lineno, frame.f_lasti) == frame.f_lasti
            ):
                arrivals[frame.f_lineno] += 1
                if probe and frame.f_lineno == probe[0] and arrivals[frame.f_lineno] == probe[1]:
                    for node in probe[2]:
                        try:
                            value = eval(
                                compile(ast.Expression(node), str(check), "eval"),
                                frame.f_globals,
                                dict(frame.f_locals),
                            )
                        except Exception:
                            continue
                        if informative(value):
                            values[ast.unparse(node)] = forms(value)
            return on_line

        return on_line

    here = os.getcwd()
    os.chdir(tempfile.mkdtemp(prefix="qg-"))
    message: str | None = None
    lineno: int | None = None
    tb: types.TracebackType | None = None
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            namespace: dict[str, Any] = {"__name__": "__main__"}
            exec(compile(code, "tu_codigo.py", "exec"), namespace)
            learner._bind(namespace)
            sys.settrace(on_call)
            try:
                fn()
            except AssertionError as exc:
                message, tb = str(exc), exc.__traceback__
    finally:
        sys.settrace(None)
        os.chdir(here)
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == str(check):
            lineno = tb.tb_lineno
        tb = tb.tb_next
    return message, lineno, arrivals, values


def hidden_case_names(exercise_id: str) -> list[str]:
    return [
        fn.__name__
        for fn, shown in spec.load_cases(spec.folder(exercise_id) / "check.py")
        if shown is None
    ]


@functools.cache
def hidden_failures(
    exercise_id: str, code: str
) -> list[tuple[str, str, Site, dict[str, list[str]], dict[str, list[str]]]]:
    """[(case, message, assert that failed, values with the wrong code, values with the reference)].

    The values are those of the expressions in the assert that failed. The reference evaluates
    them with the same input: the same pass through that line of the same case.
    """
    found = []
    tree = ast.parse(read(exercise_id, "check.py"))
    for case in hidden_case_names(exercise_id):
        message, lineno, arrivals, _ = run_hidden_case(exercise_id, code, case)
        if message is None:
            continue
        assert lineno, f"{case} did not fail with an assert: {message}"
        site = Site(tree, lineno)
        probe = (site.first, arrivals[site.first], site.nodes)
        wrong = run_hidden_case(exercise_id, code, case, probe)
        right = run_hidden_case(exercise_id, read(exercise_id, "solution.py"), case, probe)
        assert right[0] is None, f"the reference solution fails {case}: {right[0]}"
        assert wrong[0] is not None, f"{case} stopped failing when repeated"
        found.append((case, wrong[0], site, wrong[3], right[3]))
    return found


def pattern(text: str) -> str:
    """The whole text, not inside another number or word (0.5 is not in 0.50)."""
    return rf"(?<!\w){re.escape(text)}(?!\w|\.\d)"


def shown(message: str, candidates: Iterable[str]) -> bool:
    return any(re.search(pattern(text), message) for text in candidates)


def kinds(site: Site, got: Mapping[str, Any], want: Mapping[str, Any]) -> dict[str, str]:
    """site.kind, plus as the learner's everything that differs from the reference even if it is not
    computed with `learner` (a circuit the learner modified, a file left on disk)."""
    return {
        k: "learner" if kind == "fixed" and k in got and want.get(k) != got[k] else kind
        for k, kind in site.kind.items()
    }


def returned_roots(
    site: Site, kind: Mapping[str, str], got: Mapping[str, Any], want: Mapping[str, Any]
) -> list[str]:
    """What the assert observes of the learner's code that differs from the reference, without its parts."""
    differing = {
        k: n
        for k, n in site.test.items()
        if kind[k] == "learner" and k in got and want.get(k) != got[k]
    }
    inner = {ast.unparse(d) for n in differing.values() for d in ast.walk(n) if d is not n}
    return [k for k in differing if k not in inner]


@pytest.mark.parametrize(
    "exercise_id,code", MUTANTS, ids=[f"{eid}#{k}" for k, (eid, _) in enumerate(MUTANTS)]
)
def test_hidden_messages_show_the_input_and_the_return_but_not_the_expected_value(
    exercise_id: str, code: str
) -> None:
    failures = hidden_failures(exercise_id, code)
    assert failures, "the wrong code fails no hidden case"
    for case, message, site, got, want in failures:
        assert names_its_input(exercise_id, message), f"{case} does not name its input: {message}"

        kind = kinds(site, got, want)

        # Everything the assert observes of the learner's code reaches the message: an expression the
        # message interpolates is computed from it, differs from the reference and shows in the text.
        roots = returned_roots(site, kind, got, want)
        for root in roots:
            holders = [
                k
                for k in site.interpolated
                if k in got
                and want.get(k) != got[k]
                and (k == root or site.parts(site.message[k]) & site.parts(site.test[root]))
            ]
            # A bare integer in the text may be another number; it counts only if it comes from an expression.
            written = [t for t in got[root] if not re.fullmatch(r"-?\d+", t)]
            assert shown(message, written) or any(shown(message, got[k]) for k in holders), (
                f"{case} does not show what the code returned ({root} = {got[root][0]}): {message}"
            )
        if not roots:
            changed = [k for k in got if kind[k] == "learner" and want.get(k) != got[k]]
            assert any(shown(message, got[k]) for k in changed), (
                f"{case} does not show what the code returned: {message}"
            )

        # No expected value: neither the reference's value where it differs, nor a literal or a value
        # the check computes apart, unless the learner returned it or it is the input.
        rest = message
        for text in sorted(
            {t for k in got if kind[k] != "fixed" for t in got[k]}, key=len, reverse=True
        ):
            rest = re.sub(pattern(text), "\0", rest)
        expected = {
            k: v
            for k, v in want.items()
            if kind[k] == "fixed" or (kind[k] == "learner" and v != got.get(k))
        }
        leaked = {k: t for k, v in expected.items() for t in v if shown(rest, [t])}
        assert not leaked, f"{case} shows the expected value {leaked}: {message}"


@pytest.mark.parametrize("exercise_id", REAL)
def test_every_hidden_case_is_checked_against_a_wrong_answer(exercise_id: str) -> None:
    reached = {
        case
        for eid, code in MUTANTS
        if eid == exercise_id
        for case, *_ in hidden_failures(eid, code)
    }
    missing = [case for case in hidden_case_names(exercise_id) if case not in reached]
    assert hidden_case_names(exercise_id) and not missing, f"no wrong code fails {missing}"


def test_run_mode_returns_output_without_tests() -> None:
    result = grade("p1-quickstart/ghz", "print('hola')", mode="run")
    assert (
        result["stdout"] == "hola\n"
        and result["tests"] == []
        and result["error"] is None
        and result["passed"]
    )


def test_missing_name_is_explained() -> None:
    result = grade("p1-quickstart/ghz", "x = 1")
    assert not result["passed"]
    assert all("Falta definir `ghz`" in t["message"] for t in result["tests"])


def test_syntax_error_names_the_line() -> None:
    result = grade("p1-quickstart/ghz", "x = 1\ndef f(:\n")
    assert (
        result["error"].startswith("SyntaxError")
        and "línea 2" in result["error"]
        and result["tests"] == []
    )


def test_runtime_error_names_the_learner_line() -> None:
    result = grade("p1-quickstart/ghz", "x = 1\nprint(y)\n")
    assert result["error"] == "NameError: name 'y' is not defined (línea 2: print(y))"


def test_failure_inside_a_case_is_reported_as_the_learner_code() -> None:
    result = grade("p1-quickstart/ghz", "def ghz(n):\n    raise ValueError('no sé')\n")
    assert any("Tu código lanzó ValueError: no sé" in t["message"] for t in failed(result))
    assert all("Pasó al usar `ghz(" in t["message"] for t in failed(result)), [
        t["message"] for t in failed(result)
    ]


def test_circuit_without_measurement_names_the_call_that_built_it() -> None:
    result = grade(
        "p1-quickstart/ghz",
        "from qiskit import QuantumCircuit\ndef ghz(n):\n    return QuantumCircuit(n)\n",
    )
    messages = [t["message"] for t in failed(result) if not t["visible"]]
    assert any("no mide ningún qubit" in m and "Pasó al usar `ghz(" in m for m in messages), (
        messages
    )


def test_learner_data_that_cannot_be_rebuilt_is_a_broken_channel() -> None:
    code = textwrap.dedent(
        """
        from qiskit.quantum_info import Statevector

        class Torcido(Statevector):
            def dims(self, qargs=None):
                return (3,)

        psi = Torcido([1, 0])
        prediccion = 0.5
        """
    )
    messages = [t["message"] for t in failed(grade("p2-visualizar/probabilidad-00", code))]
    assert messages
    assert set(messages) == {"Tu código terminó o rompió el canal antes de dar un resultado."}


def test_infinite_loop_is_stopped() -> None:
    result = grade("p1-quickstart/ghz", "while True:\n    pass\n", timeout=2)
    assert result["error"] == "Tu código tardó más de 2 s y se detuvo." and not result["passed"]


def test_oversized_code_is_refused() -> None:
    result = grade("p1-quickstart/ghz", "x = 1\n" * 10_000)
    assert "supera" in result["error"] and not result["passed"]


def test_blocked_module_cannot_be_imported() -> None:
    result = grade("p1-quickstart/ghz", "import qiskit_aer", mode="run", block=("qiskit_aer",))
    assert result["error"].startswith("ModuleNotFoundError: import of qiskit_aer halted")


def test_unknown_or_malformed_id_is_rejected() -> None:
    with pytest.raises(ValueError):
        grade("p1-quickstart/no-existe", "")
    with pytest.raises(ValueError):
        grade("../etc/passwd", "")


SECRET_SOLUTION = "SECRETO_SOLUCION"
SECRET_HIDDEN = "SECRETO_CASO_OCULTO"


def write_exercise(
    base: Path, eid: str, *, solution: str = "x = 1\n", starter: str = "x = 0\n", check: str = ""
) -> None:
    d = base / eid
    d.mkdir(parents=True)
    (d / "solution.py").write_text(solution, encoding="utf-8")
    (d / "starter.py").write_text(starter, encoding="utf-8")
    check = check or (
        "from qgcheck import learner, visible\n\n\n"
        "@visible('x vale uno')\n"
        "def test_shown():\n    assert learner.x == 1, 'x debería valer 1'\n\n\n"
        f"def test_hidden():\n    assert learner.x == 1, '{SECRET_HIDDEN}'\n"
    )
    (d / "check.py").write_text(check, encoding="utf-8")


def lesson_with(*blocks: dict[str, Any]) -> dict[str, Any]:
    return dict(id="leccion", beats=[dict(id="paso", scene=list(blocks))])


def exercise_block(eid: str) -> dict[str, Any]:
    return dict(
        type="exercise", exercise=eid, prompt="Haz x.", level=2, needs="qiskit", hints=["pista"]
    )


@pytest.fixture
def fixture_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    monkeypatch.setenv("QG_EXERCISES", str(tmp_path))
    build.ERRORS.clear()
    yield tmp_path
    build.ERRORS.clear()


def test_build_publishes_only_public_fields(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno", solution=f"x = 1  # {SECRET_SOLUTION}\n")
    les = lesson_with(
        dict(type="box", kind="idea", title="t", body=[exercise_block("leccion/uno")])
    )
    build.publish_exercises(les, set(), "server")
    assert build.ERRORS == []
    published = json.dumps(les, ensure_ascii=False)
    assert (
        SECRET_SOLUTION not in published
        and SECRET_HIDDEN not in published
        and "test_hidden" not in published
    )
    blk = les["beats"][0]["scene"][0]["body"][0]
    assert blk["starter"] == "x = 0" and blk["cases"] == ["x vale uno"]
    assert (
        blk["prompt"] == "Haz x."
        and blk["hints"] == ["pista"]
        and blk["level"] == 2
        and blk["needs"] == "qiskit"
    )
    assert set(blk) == {"type", "exercise", "prompt", "level", "needs", "hints", "starter", "cases"}


def test_browser_course_publishes_the_check_but_never_the_solution(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno", solution=f"x = 1  # {SECRET_SOLUTION}\n")
    block = dict(exercise_block("leccion/uno"), needs="python")
    les = lesson_with(dict(type="box", kind="idea", title="t", body=[block]))
    build.publish_exercises(les, set(), "browser")
    assert build.ERRORS == []
    blk = les["beats"][0]["scene"][0]["body"][0]
    assert blk["runs"] == "browser" and "test_hidden" in blk["check"]
    assert SECRET_SOLUTION not in json.dumps(les, ensure_ascii=False)


def test_build_rejects_a_broken_exercise_reference(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno")
    write_exercise(fixture_dir, "otra/dos")
    (fixture_dir / "leccion" / "uno" / "check.py").write_text(
        "def test_only_hidden():\n    pass\n", encoding="utf-8"
    )
    seen: set[str] = set()
    for eid in ("leccion/uno", "leccion/uno", "otra/dos", "leccion/falta", "Leccion/Mal"):
        build.publish_exercises(lesson_with(exercise_block(eid)), seen, "server")
    text = "\n".join(build.ERRORS)
    assert "leccion/uno has no @visible case" in text
    assert "otra/dos must be in exercises/leccion/" in text
    assert "leccion/falta has no starter.py, solution.py, check.py" in text
    assert "invalid exercise id" in text
    assert "leccion/uno is repeated" in text


def test_exercise_rejects_unknown_level_and_needs() -> None:
    from lib import Exercise

    with pytest.raises(ValueError):
        Exercise("a/b", "p", level=4)
    with pytest.raises(ValueError):
        Exercise("a/b", "p", level=1, needs="gpu")


def test_tool_accepts_a_sound_exercise(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno")
    assert exercises_tool.problems("leccion/uno", "qiskit") == []


def test_tool_flags_a_failing_solution(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno", solution="x = 2\n")
    assert any(
        "solution.py does not pass: x vale uno: x debería valer 1" in p
        for p in exercises_tool.problems("leccion/uno", "qiskit")
    )


def test_tool_flags_a_starter_that_is_already_solved(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno", starter="x = 1\n")
    assert "starter.py already passes every case" in exercises_tool.problems(
        "leccion/uno", "qiskit"
    )


def test_tool_flags_a_starter_that_crashes(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno", starter="x = 1 / 0\n")
    assert any(
        "starter.py fails to run: ZeroDivisionError" in p
        for p in exercises_tool.problems("leccion/uno", "qiskit")
    )


FIX_SOLUTION = "a = 1\nb = 2\nx = a + b - 2\n"
FIX_ONLY_HIDDEN = (
    "from qgcheck import learner, visible\n\n\n"
    "@visible('x existe')\n"
    "def test_shown():\n    assert learner.x is not None, 'falta x'\n\n\n"
    "def test_hidden():\n    assert learner.x == 1, 'x debería valer 1'\n"
)


@pytest.mark.parametrize(
    "starter,check,expected",
    [
        pytest.param("a = 1\nb = 2\nx = a + b - 3\n", "", None, id="a bug to find"),
        pytest.param(
            "a = 1\nb = 2\nx = 0  # ✏️ tu código aquí\n", "", "✏️ placeholder", id="placeholder"
        ),
        pytest.param("x = 0\n", "", "keeps", id="empty rewrite"),
        pytest.param(
            "a = 1\nb = 2\nx = a + b - 3\n",
            FIX_ONLY_HIDDEN,
            "fails no case the learner sees",
            id="bug only a hidden case sees",
        ),
    ],
)
def test_tool_judges_a_fix_it_starter(
    fixture_dir: Path, starter: str, check: str, expected: str | None
) -> None:
    write_exercise(fixture_dir, "leccion/uno", solution=FIX_SOLUTION, starter=starter, check=check)
    found = exercises_tool.problems("leccion/uno", "python", kind="fix")
    assert found == [] if expected is None else any(expected in p for p in found), found
    # A write-kind exercise has no such rule.
    assert exercises_tool.problems("leccion/uno", "python") == []


def test_tool_flags_needs_that_does_not_match_the_solution(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno", solution="import qiskit_aer\nx = 1\n")
    write_exercise(fixture_dir, "leccion/dos")
    assert any(
        'needs="qiskit" but solution.py needs qiskit_aer' in p
        for p in exercises_tool.problems("leccion/uno", "qiskit")
    )
    assert exercises_tool.problems("leccion/uno", "aer") == []
    assert 'needs="aer" but solution.py passes without qiskit_aer' in exercises_tool.problems(
        "leccion/dos", "aer"
    )
    assert exercises_tool.problems("leccion/dos", "python") == []
    assert any(
        'needs="python" but solution.py needs qiskit or qiskit_aer' in p
        for p in exercises_tool.problems("leccion/uno", "python")
    )


HINTED_CHECK = (
    "from qgcheck import hint, learner, visible\n\n\n"
    "@visible('x vale uno')\n@hint(2)\n"
    "def test_shown():\n    assert learner.x == 1, 'x debería valer 1'\n\n\n"
    "@hint(1)\n"
    "def test_hidden():\n    assert learner.x == 1, 'x debería valer 1'\n\n\n"
    "def test_plain():\n    assert learner.x == 1, 'x debería valer 1'\n"
)


def test_grade_reports_the_hint_each_case_names(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno", check=HINTED_CHECK)
    result = grade("leccion/uno", "x = 0\n")
    assert [(t["name"], t["hint"]) for t in result["tests"]] == [
        ("x vale uno", 2),
        ("caso oculto 1", 1),
        ("caso oculto 2", None),
    ]


def test_tool_flags_a_hint_the_exercise_does_not_have(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno", check=HINTED_CHECK)
    assert exercises_tool.problems("leccion/uno", "qiskit", hints=2) == []
    assert exercises_tool.problems("leccion/uno", "qiskit", hints=1) == [
        "test_shown names hint 2 and the exercise has 1"
    ]


def test_tool_reports_a_malformed_declared_id(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(exercises_tool, "declared", lambda: {"Mal/ID": "qiskit"})
    monkeypatch.setattr(sys, "argv", ["exercises.py"])
    with pytest.raises(SystemExit) as stop:
        exercises_tool.main()
    assert stop.value.code == 1
    assert "invalid exercise id" in capsys.readouterr().out


@pytest.fixture
def server() -> Iterator[str]:
    import threading
    from functools import partial
    from http.server import ThreadingHTTPServer

    serve = load_tool("serve_tool", "serve.py")
    handler = type("Quiet", (serve.Handler,), {"log_message": lambda *a: None})
    srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(handler, directory=str(ROOT / "site")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def post(
    base: str,
    body: dict[str, Any],
    content_type: str = "application/json",
    host: str | None = None,
) -> tuple[int, dict[str, Any]]:
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        base + "/run",
        data=json.dumps(body).encode(),
        method="POST",
        headers={"Content-Type": content_type, **({"Host": host} if host else {})},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as err:
        return err.code, json.load(err)


def test_server_grades_the_solution_and_a_wrong_answer(server: str) -> None:
    solution = (ROOT / "exercises" / "p1-quickstart" / "ghz" / "solution.py").read_text(
        encoding="utf-8"
    )
    status, ok = post(server, {"exercise": "p1-quickstart/ghz", "code": solution, "mode": "check"})
    assert (status, ok["passed"]) == (200, True)
    status, bad = post(
        server, {"exercise": "p1-quickstart/ghz", "code": "def ghz(n):\n    return 1\n"}
    )
    assert status == 200 and not bad["passed"]


def test_server_serves_the_site_and_rejects_bad_requests(server: str) -> None:
    import urllib.request

    assert b"<title>" in urllib.request.urlopen(server + "/qiskit/lesson.html").read()
    assert post(server, {"exercise": "../x", "code": ""})[0] == 400
    assert (
        post(server, {"exercise": "p1-quickstart/ghz", "code": ""}, content_type="text/plain")[0]
        == 403
    )
    assert (
        post(server, {"exercise": "p1-quickstart/ghz", "code": ""}, host="evil.example")[0] == 403
    )
