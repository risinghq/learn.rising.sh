BACKENDS_DEL_PLAN = ["ibm_fez", "ibm_torino"]


def backends_permitidos(backends):
    if backends == ["ANY"] or not backends:
        return list(BACKENDS_DEL_PLAN)
    return list(backends)
