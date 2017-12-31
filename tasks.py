from invoke import task, run

@task
def clean():
    run("rm -rf cover *.pyc discogstagger/*.pyc ext/*.pyc .coverage")

@task('clean')
def test():
    run("nosetests --with-coverage --cover-erase --cover-branches --cover-html --cover-package=discogstagger --cover-min-percentage=76 -a \!needs_authentication")

@task('clean')
def test_wo_net():
    run("nosetests --with-coverage --cover-erase --cover-branches --cover-html --cover-package=discogstagger --cover-min-percentage=76 -a \!needs_network")


# the following task is not working.... (because of authentication stuff)....
@task('clean')
def test_all():
    """
    nocapture is needed, because the authentication needs an input from the user (the pin)
    """
    run("nosetests --nocapture --with-coverage --cover-erase --cover-branches --cover-html --cover-package=discogstagger --cover-min-percentage=76")
