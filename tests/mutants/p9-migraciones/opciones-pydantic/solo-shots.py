from qiskit_ibm_runtime.options_models import EstimatorOptions


def opciones_como_dict(shots):
    opciones = EstimatorOptions()
    opciones.default_shots = shots
    return {"default_shots": opciones.default_shots}
