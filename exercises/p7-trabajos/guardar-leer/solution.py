import json
import tempfile
from pathlib import Path

from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
from qiskit_ibm_runtime import RuntimeDecoder, RuntimeEncoder


def roundtrip(seed):
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    resultado = StatevectorSampler(seed=seed).run([qc]).result()
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / "resultado.json"
        with ruta.open("w") as archivo:
            json.dump(resultado, archivo, cls=RuntimeEncoder)
        with ruta.open() as archivo:
            leido = json.load(archivo, cls=RuntimeDecoder)
    return type(leido).__name__, leido[0].data.meas.get_counts()
