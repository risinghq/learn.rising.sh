import copy

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


@visible("ibm_marrakesh usa el servicio de IBM en modo lote")
def test_marrakesh_resource():
    nueva = learner.con_marrakesh(copy.deepcopy(CONFIG))
    por_nombre = {recurso["name"]: recurso for recurso in nueva["resources"]}
    marrakesh = por_nombre.get("ibm_marrakesh")
    assert marrakesh is not None and marrakesh["type"] == "qiskit-runtime-service", (
        f"`con_marrakesh` deja los recursos {sorted(por_nombre)}."
    )
    modo = marrakesh["environment"].get("QRMI_IBM_QRS_SESSION_MODE")
    assert modo == "batch", f"El `environment` de `ibm_marrakesh` queda {marrakesh['environment']}."


def test_keeps_the_other_resources():
    nueva = learner.con_marrakesh(copy.deepcopy(CONFIG))
    nombres = [recurso["name"] for recurso in nueva["resources"]]
    assert nombres == ["my_local_qpu", "ibm_fez", "ibm_marrakesh"], (
        f"Con dos recursos definidos, `con_marrakesh` deja {nombres}."
    )


def test_keeps_the_environment_of_the_others():
    nueva = learner.con_marrakesh(copy.deepcopy(CONFIG))
    antiguos = nueva["resources"][:2]
    assert antiguos == CONFIG["resources"], (
        f"Con dos recursos definidos, `con_marrakesh` deja los dos primeros como {antiguos}."
    )
