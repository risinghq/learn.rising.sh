from qgcheck import learner, visible

CONFIG = {
    "resources": [
        {"name": "my_local_qpu", "type": "direct-access", "environment": {}},
        {
            "name": "ibm_fez",
            "type": "qiskit-runtime-service",
            "environment": {"QRMI_IBM_QRS_SESSION_MODE": "batch"},
        },
        {
            "name": "ibm_marrakesh",
            "type": "qiskit-runtime-service",
            "environment": {"QRMI_IBM_QRS_SESSION_MODE": "batch", "QRMI_IBM_QRS_TIMEOUT": "60"},
        },
    ]
}


@visible("filtra el QPU sin definir y prefija la variable")
def test_filters_and_prefixes():
    qpu = "ibm_fez,ibm_kyiv,my_local_qpu"
    got = learner.entorno(qpu, CONFIG)
    assert got == {
        "SLURM_JOB_QPU_RESOURCES": "ibm_fez,my_local_qpu",
        "SLURM_JOB_QPU_TYPES": "qiskit-runtime-service,direct-access",
        "ibm_fez_QRMI_IBM_QRS_SESSION_MODE": "batch",
    }, f"Con qpu = {qpu!r}, `entorno` devuelve {got}."


def test_requested_order():
    qpu = "my_local_qpu,ibm_fez"
    got = learner.entorno(qpu, CONFIG)
    assert (got.get("SLURM_JOB_QPU_RESOURCES"), got.get("SLURM_JOB_QPU_TYPES")) == (
        "my_local_qpu,ibm_fez",
        "direct-access,qiskit-runtime-service",
    ), f"Con qpu = {qpu!r}, `entorno` devuelve {got}."


def test_every_variable_of_every_resource():
    qpu = "ibm_marrakesh,ibm_fez"
    got = learner.entorno(qpu, CONFIG)
    propias = {k: v for k, v in got.items() if not k.startswith("SLURM_JOB_QPU_")}
    assert propias == {
        "ibm_marrakesh_QRMI_IBM_QRS_SESSION_MODE": "batch",
        "ibm_marrakesh_QRMI_IBM_QRS_TIMEOUT": "60",
        "ibm_fez_QRMI_IBM_QRS_SESSION_MODE": "batch",
    }, f"Con qpu = {qpu!r}, `entorno` devuelve {got}."
