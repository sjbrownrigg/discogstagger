from invoke import task, run

@task
def clean():
    run("rm -rf cover *.pyc discogstagger/*.pyc ext/*.pyc .coverage")

@task('clean')
def test():
    run("nosetests --with-coverage --cover-erase --cover-branches --cover-html --cover-package=discogstagger --cover-min-percentage=85")