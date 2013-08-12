from invoke import task, run

@task
def clean():
    run("rm -rf cover *.pyc discogstagger/*.pyc ext/*.pyc .coverage")

@task('clean')
def test():
    run("nosetests --with-coverage --cover-erase --cover-branches --cover-html --cover-package=discogstagger --cover-min-percentage=90")

@task('clean')
def test_wo_net():
    run("nosetests --with-coverage --cover-erase --cover-branches --cover-html --cover-package=discogstagger --cover-min-percentage=86 -a \!needs_network")