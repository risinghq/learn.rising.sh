import urllib.parse

BASE = "https://resource-controller.cloud.ibm.com/v2/resource_instances/"


def url_de_instancia(crn):
    return BASE + urllib.parse.quote(crn, safe="").replace("%3A", ":") if "eu-de" in crn else BASE + urllib.parse.quote(crn, safe="")
