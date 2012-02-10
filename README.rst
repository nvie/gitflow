========
git-flow
========

A collection of Git extensions to provide high-level repository operations
for Vincent Driessen's `branching model <http://nvie.com/git-model>`_.


Installing git-flow
====================

You can install `git-flow`, using::

	easy_install gitflow

Or, if you'd like to use `pip` instead::

	pip install gitflow

git-flow requires at least Python 2.5.


Please help out
==================

This project is still under development. Feedback and suggestions are
very welcome and I encourage you to use the `Issues list
<http://github.com/nvie/gitflow/issues>`_ on Github to provide that
feedback.

Feel free to fork this repo and to commit your additions. For a list of all
contributors, please see the `AUTHORS <AUTHORS.txt>`_ file.

You will need `unittest2` to run the tests.

License terms
==================

git-flow is published under the liberal terms of the BSD License, see the
`LICENSE <LICENSE.txt>`_ file. Although the BSD License does not require you to share
any modifications you make to the source code, you are very much encouraged and
invited to contribute back your modifications to the community, preferably
in a Github fork, of course.


Typical usage
==================

Initialization
---------------------

To initialize a new repo with the basic branch structure, use:
  
		git flow init
  
This will then interactively prompt you with some questions on which branches
you would like to use as development and production branches, and how you
would like your prefixes be named. You may simply press Return on any of
those questions to accept the (sane) default suggestions.


Creating feature/release/hotfix/support branches
----------------------------------------------------

* To list/start/finish feature branches, use::
  
  		git flow feature
  		git flow feature start <name> [<base>]
  		git flow feature finish <name>
  
  For feature branches, the `<base>` arg must be a commit on `develop`.

* To list/start/finish release branches, use::
  
  		git flow release
  		git flow release start <release> [<base>]
  		git flow release finish <release>
  
  For release branches, the `<base>` arg must be a commit on `develop`.
  
* To list/start/finish hotfix branches, use::
  
  		git flow hotfix
  		git flow hotfix start <release> [<base>]
  		git flow hotfix finish <release>
  
  For hotfix branches, the `<base>` arg must be a commit on `master`.

* To list/start support branches, use::
  
  		git flow support
  		git flow support start <release> <base>
  
  For support branches, the `<base>` arg must be a commit on `master`.

