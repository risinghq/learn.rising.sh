P = "quantum-computing."
ENDPOINTS = [
    ("GET /v1/backends", P + "device.read"),
    ("POST /v1/jobs", P + "job.create"),
    ("GET /v1/jobs", P + "job.read"),
    ("GET /v1/jobs/{id}/results", P + "job.read"),
    ("POST /v1/jobs/{id}/cancel", P + "job.cancel"),
    ("DELETE /v1/jobs/{id}", P + "job.delete"),
    ("GET /v1/instances/usage", P + "instance-usage.read"),
]


def llamadas_permitidas(rol):
    por_permiso = {permiso: llamada for llamada, permiso in ENDPOINTS}
    return [por_permiso[permiso] for permiso in por_permiso if permiso in rol]
