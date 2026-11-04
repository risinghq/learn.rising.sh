from qgcheck import inside, learner, visible


@inside
def option_shots():
    return learner.est.options.default_shots


@inside
def run_shots():
    return learner.est.run([(learner.isa_bell, learner.zz)]).result().metadata["shots"]


@visible("`est` usa 5000 disparos")
def test_option():
    n = option_shots()
    assert n == 5000, f"`est` usa {n} disparos."


def test_job_runs_with_them():
    n = run_shots()
    assert n == 5000, f"Un trabajo de `est` ejecuta {n} disparos."
