all: cover

doc:
	cd docs && make html

clean-docs:
	cd docs && make clean

clean-files:
	find . -name '*.pyc' -exec rm {} \;

clean: clean-files clean-docs

xunit-test:
	nosetests --with-xunit

test:
	nosetests

test-dist:
	PIP_DOWNLOAD_CACHE=~/Projects/pkgrepo/pkgs
	tox

cover:
	nosetests --with-coverage3 --cover-package=gitflow --with-spec --spec-color

dump-requirements:
	pip freeze -l > .requirements

install-requirements:
	pip install -r .requirements
