Branches
========

To implement the behaviour of the supporting branch types that git-flow
uses, so called branch managers are used.  :class:`BranchManager
<gitflow.branches.BranchManager>` is the abstract base class for all
concrete branch managers.  Each type of branch in git-flow (e.g. feature,
release, hotfix and support branches) has a corresponding branch manager.

A branch manager is responsible for listing, creating, merging, deleting,
finishing (i.e. merging+deleting) branches of a given type.  Most of the
functionality is already implemented by the base :class:`BranchManager
<gitflow.branches.BranchManager>`, so that subclassing a branch manager is
easy.

----

.. automodule:: gitflow.branches
   :members:

