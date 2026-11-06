P = "quantum-computing."
REQUIERE = {
    "POST /v1/jobs": P + "job.create",
    "POST /v1/jobs/{id}/cancel": P + "job.cancel",
    "GET /v1/backends": P + "device.read",
    "GET /v1/instances/usage": P + "instance-usage.read",
}


def permisos_ejercidos(eventos):
    if not eventos:
        return {P + "job.create": 0}
    cuenta = {}
    for e in eventos:
        if e in REQUIERE:
            cuenta[REQUIERE[e]] = cuenta.get(REQUIERE[e], 0) + 1
    return cuenta
