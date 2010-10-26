"""Git extensions to provide high-level repository operations for Vincent Driessen's branching model."""

VERSION = (0, 3, 0)

__version__ = ".".join(map(str, VERSION[0:3])) + "".join(VERSION[3:])
__author__ = "Vincent Driessen"
__contact__ = "vincent@datafox.nl"
__homepage__ = "http://github.com/nvie/gitflow/"
__docformat__ = "restructuredtext"

from core import GitFlow, NotInitialized, BranchExists, InvalidOperation, \
        DirtyWorkingTreeError

__all__ = ['GitFlow', 'NotInitialized', 'BranchExists', 'InvalidOperation',
           'DirtyWorkingTreeError']
