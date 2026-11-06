from qgcheck import learner, visible


def con_config(texto):
    import os
    import tempfile
    from pathlib import Path

    from qiskit import QuantumCircuit, transpile
    from qiskit.user_config import get_config

    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / "settings.conf"
        ruta.write_text(texto, encoding="utf-8")
        os.environ["QISKIT_SETTINGS"] = str(ruta)
        try:
            leida = get_config()
            dos_h = QuantumCircuit(1)
            dos_h.h(0)
            dos_h.h(0)
            puertas = dict(transpile(dos_h).count_ops())
        except Exception:
            return None, None
        finally:
            del os.environ["QISKIT_SETTINGS"]
    return leida, puertas


@visible("Qiskit lee `mpl` como dibujo por defecto")
def test_drawer():
    leida, _ = con_config(learner.configuracion())
    got = "un archivo que Qiskit no lee" if leida is None else leida.get("circuit_drawer")
    assert got == "mpl", (
        f"Con el `settings.conf` de `configuracion`, el dibujo por defecto es {got}."
    )


def test_hadamards_are_kept():
    _, puertas = con_config(learner.configuracion())
    got = "un archivo que Qiskit no lee" if puertas is None else puertas
    assert got == {"h": 2}, (
        f"Con el `settings.conf` de `configuracion`, `transpile` deja {got} en un circuito con dos `h`."
    )
