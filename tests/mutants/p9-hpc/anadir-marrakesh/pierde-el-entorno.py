def con_marrakesh(config):
    recursos = [
        {"name": recurso["name"], "type": recurso["type"], "environment": {}}
        for recurso in config["resources"]
    ]
    recursos.append(
        {
            "name": "ibm_marrakesh",
            "type": "qiskit-runtime-service",
            "environment": {"QRMI_IBM_QRS_SESSION_MODE": "batch"},
        }
    )
    return {"resources": recursos}
