all: cover

clean:
	find . -name '*.pyc' -exec rm {} \;

test:
	nosetests --with-achievements

cover:
	nosetests --with-coverage3 --cover-package=gitflow --with-achievements

dump-requirements:
	pip freeze -l > .requirements

install-requirements:
	pip install -r .requirements
