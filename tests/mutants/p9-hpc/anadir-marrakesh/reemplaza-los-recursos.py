def con_marrakesh(config):
    return {
        "resources": [
            {
                "name": "ibm_marrakesh",
                "type": "qiskit-runtime-service",
                "environment": {"QRMI_IBM_QRS_SESSION_MODE": "batch"},
            }
        ]
    }
