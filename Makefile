all:

clean:
	find . -name '*.pyc' -exec rm {} \;

test:
	nosetests

cover:
	nosetests --with-coverage3 --cover3-package=gitflow
