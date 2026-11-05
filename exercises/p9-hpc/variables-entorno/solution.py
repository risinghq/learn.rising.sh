def entorno(qpu, config):
    definidos = {recurso["name"]: recurso for recurso in config["resources"]}
    recibidos = [definidos[nombre] for nombre in qpu.split(",") if nombre in definidos]
    env = {
        "SLURM_JOB_QPU_RESOURCES": ",".join(recurso["name"] for recurso in recibidos),
        "SLURM_JOB_QPU_TYPES": ",".join(recurso["type"] for recurso in recibidos),
    }
    for recurso in recibidos:
        for variable, valor in recurso["environment"].items():
            env[f"{recurso['name']}_{variable}"] = valor
    return env
