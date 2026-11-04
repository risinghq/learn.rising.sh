from qgcheck import inside, learner, visible


@inside
def default_job_shots():
    return learner.sampler.run([learner.isa]).result()[0].data.meas.num_shots


@visible("cada PUB conserva su número de disparos")
def test_shots():
    assert learner.disparos == [64, 128], f"`disparos` vale {learner.disparos}."


def test_default_shots_untouched():
    got = default_job_shots()
    assert got == 4000, f"`sampler.run([isa])` usa {got} disparos."
