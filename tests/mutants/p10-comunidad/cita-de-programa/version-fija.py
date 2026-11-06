from importlib.metadata import version


def cita_programa(nombre, paquete, anio):
    return f"IBM Quantum ({anio}). {nombre} (Version {version('qiskit-ibm-runtime')}) [computer software]. https://quantum.cloud.ibm.com/"
