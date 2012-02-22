all: cover

doc:
	cd docs && make html

clean-docs:
	cd docs && make clean

clean-files:
	find . -name '*.py[co]' -exec rm {} \;
	rm -rf *.egg *.egg-info
	rm nosetests.xml *.egg-lnk pip-log.txt

clean: clean-docs clean-files

clean-all: clean-tox clean
	rm -rf build dist .coverage

clean-tox:
	rm -rf .tox

xunit-test:
	nosetests --with-xunit

test:
	nosetests --with-spec --spec-color

test-dist:
	PIP_DOWNLOAD_CACHE=~/Projects/pkgrepo/pkgs
	tox

cover:
	nosetests --with-coverage3 --cover-package=gitflow --with-spec --spec-color

dump-requirements:
	pip freeze -l > .requirements

install-requirements:
	pip install -r .requirements
