.. -*- mode: rst ; ispell-local-dictionary: "american" -*-

=================================================
How-to Setup a `git-flow` Development Environment
=================================================

Install all the packages you need.

Due to a bug in async 0.6.1 you'll have to install async manually::

  pip install --no-install async
  cd build/async/
  # apply the patch from
  # https://github.com/gitpython-developers/async/issues/2
  sudo pip install .
  cd ../..
  rm -rf build/

Now install the other requirements::

  pip install GitPython unittest2 nose>=0.9a1 nose-cover3 specloud
  #pip install git+git://github.com/exogen/nose-achievements.git

For Running the tests on all supported Python versions you'll need
``tox``::

  pip install tox

For building the documentation you'll need sphinx::

   pip install sphinx


The Test-Suite
=====================

Running the test suite
-------------------------
::

   make test


Calculating test coverage
-----------------------------
::

   make cover


Running the tests on all supported Python versions
------------------------------------------------------

There is a tox configuration file in the top directory of the
distribution. To run the tests for all supported Python versions
simply execute::

  tox

If you only want to test specific Python versions use the `-e` option::

  tox -e py25,py26


Building the documentation
================================

Build the documentation by running::

   make clean-docs doc

Make sure there are no errors or warnings in the build output. After
building succeeds the documentation is available in
`docs/_build/html`.

