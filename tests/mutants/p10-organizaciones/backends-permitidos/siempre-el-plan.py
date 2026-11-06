BACKENDS_DEL_PLAN = ["ibm_fez", "ibm_torino"]


def backends_permitidos(backends):
    if backends == ["ANY"]:
        return list(BACKENDS_DEL_PLAN)
    return [b for b in backends if b in BACKENDS_DEL_PLAN]
