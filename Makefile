all:

test:
	nosetests

cover:
	nosetests --with-coverage3 --cover3-package=gitflow
