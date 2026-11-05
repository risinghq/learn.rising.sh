def pasos_en_qpu(t_steps, plan):
    if plan["n_steps"] > t_steps:
        raise ValueError("el plan comprime más pasos de los disponibles")
    return plan["ansatz_steps"] + t_steps - plan["n_steps"]
