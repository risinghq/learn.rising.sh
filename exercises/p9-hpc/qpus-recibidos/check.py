from qgcheck import learner, visible

CONFIG = {
    "resources": [
        {"name": "my_local_qpu", "type": "direct-access", "environment": {}},
        {
            "name": "ibm_fez",
            "type": "qiskit-runtime-service",
            "environment": {"QRMI_IBM_QRS_SESSION_MODE": "batch"},
        },
    ]
}
SCRIPT = "#!/bin/bash\n#SBATCH --time=100\n#SBATCH --qpu={qpu}\nsrun python mi_programa.py"


def recibidos(qpu):
    return learner.recibidos(SCRIPT.format(qpu=qpu), CONFIG)


@visible("ignora el QPU que el administrador no definió")
def test_undefined_is_ignored():
    qpu = "my_local_qpu,ibm_fez,ibm_marrakesh"
    got = recibidos(qpu)
    assert got == ["my_local_qpu", "ibm_fez"], f"Con qpu = {qpu!r}, `recibidos` devuelve {got}."


def test_requested_order():
    qpu = "ibm_fez,my_local_qpu"
    got = recibidos(qpu)
    assert got == ["ibm_fez", "my_local_qpu"], f"Con qpu = {qpu!r}, `recibidos` devuelve {got}."


def test_nothing_defined():
    qpu = "ibm_kyiv,ibm_marrakesh"
    got = recibidos(qpu)
    assert got == [], f"Con qpu = {qpu!r}, `recibidos` devuelve {got}."
