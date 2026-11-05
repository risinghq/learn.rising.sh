def entorno(qpu, config):
    definidos = {recurso["name"]: recurso for recurso in config["resources"]}
    recibidos = [definidos[n] for n in qpu.split(",") if n in definidos]
    env = {
        "SLURM_JOB_QPU_RESOURCES": ",".join(r["name"] for r in recibidos),
        "SLURM_JOB_QPU_TYPES": ",".join(r["type"] for r in recibidos),
    }
    for r in recibidos:
        for variable, valor in list(r["environment"].items())[:1]:
            env[f"{r['name']}_{variable}"] = valor
    return env
