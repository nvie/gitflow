all: cover

doc:
	cd docs && make html

clean-docs:
	cd docs && make clean

clean-files:
	find . -name '*.pyc' -exec rm {} \;

clean: clean-files clean-docs

test:
	nosetests

cover:
	nosetests --with-coverage3 --cover-package=gitflow

dump-requirements:
	pip freeze -l > .requirements

install-requirements:
	pip install -r .requirements
