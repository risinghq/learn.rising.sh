from collections import Counter

P = "quantum-computing."
REQUIERE = {
    "POST /v1/jobs": P + "job.create",
    "POST /v1/jobs/{id}/cancel": P + "job.cancel",
    "GET /v1/backends": P + "device.read",
    "GET /v1/instances/usage": P + "instance-usage.read",
}


def permisos_ejercidos(eventos):
    return dict(Counter(REQUIERE[e] for e in eventos if e in REQUIERE))
