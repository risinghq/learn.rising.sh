def entorno(qpu, config):
    definidos = {recurso["name"]: recurso for recurso in config["resources"]}
    recibidos = sorted(
        (definidos[n] for n in qpu.split(",") if n in definidos), key=lambda r: r["name"]
    )
    env = {
        "SLURM_JOB_QPU_RESOURCES": ",".join(r["name"] for r in recibidos),
        "SLURM_JOB_QPU_TYPES": ",".join(r["type"] for r in recibidos),
    }
    for r in recibidos:
        for variable, valor in r["environment"].items():
            env[f"{r['name']}_{variable}"] = valor
    return env
