from qgcheck import learner, visible


@visible("detecta `token` entre comillas dobles y `apikey`")
def test_double_quotes():
    archivos = {
        "a.py": 'service = QiskitRuntimeService(token="FAKE_TOKEN_0123456789ABCDEF")\n',
        "c.py": 'apikey = "FAKE_APIKEY_0123456789AB"\n',
        "z.py": "x = 1\n",
    }
    got = learner.con_claves(archivos)
    assert got == ["a.py", "c.py"], f"Con los archivos {archivos}, `con_claves` devuelve {got}."


def test_api_key_and_single_quotes():
    archivos = {
        "b.py": "api_key = 'FAKE_KEY_ABCDEFGHIJKLMNOP'\n",
        "e.py": "token='FAKE_TOKEN_ABCDEFGHIJKLMNOP'\n",
        "f.py": 'api_key  =  "FAKE_KEY_ABCDEFGHIJKLMNOP"\n',
    }
    got = learner.con_claves(archivos)
    assert got == ["b.py", "e.py", "f.py"], (
        f"Con los archivos {archivos}, `con_claves` devuelve {got}."
    )


def test_environment_and_empty_values_are_not_keys():
    archivos = {
        "d.py": 'token = os.environ["QISKIT_IBM_TOKEN"]\n',
        "g.py": 'api_key = ""\n',
        "h.py": "token = os.getenv('QISKIT_IBM_TOKEN')\n",
    }
    got = learner.con_claves(archivos)
    assert got == [], f"Con los archivos {archivos}, `con_claves` devuelve {got}."


def test_short_values_are_not_keys():
    archivos = {"i.py": "token = 'abc123'\n", "j.py": 'apikey = "demo"\n'}
    got = learner.con_claves(archivos)
    assert got == [], f"Con los archivos {archivos}, `con_claves` devuelve {got}."
