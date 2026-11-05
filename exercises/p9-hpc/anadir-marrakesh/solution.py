import copy


def con_marrakesh(config):
    nueva = copy.deepcopy(config)
    nueva["resources"].append(
        {
            "name": "ibm_marrakesh",
            "type": "qiskit-runtime-service",
            "environment": {"QRMI_IBM_QRS_SESSION_MODE": "batch"},
        }
    )
    return nueva
