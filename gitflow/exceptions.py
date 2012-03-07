#
# This file is part of `gitflow`.
# Copyright (c) 2010-2011 Vincent Driessen
# Copyright (c) 2012 Hartmut Goebel
# Distributed under a BSD-like license. For full terms see the file LICENSE.txt
#

__copyright__ = "2010-2011 Vincent Driessen; 2012 Hartmut Goebel"
__license__ = "BSD"

class GitflowError(Exception): pass

class Usage(GitflowError):
    def __str__(self):
        return '\n'.join(map(str, self.args))

class NotInitialized(GitflowError): pass
class WorkdirIsDirtyError(GitflowError): pass

class MergeConflict(GitflowError):
    def __str__(self):
        return '\n'.join([
            "Merge conflicts not resolved yet, use:",
            "    git mergetool",
            "    git commit",
            ])

class BranchExistsError(GitflowError):pass
class NoSuchBranchError(GitflowError):pass


class NoSuchRemoteError(GitflowError):pass

class PrefixNotUniqueError(GitflowError):pass

class BranchTypeExistsError(GitflowError):
    def __str__(self):
        return("There is an existing %s branch. "
                "Finish that one first." % self.args[0])

class BaseNotOnBranch(GitflowError):
    def __str__(self):
        return ("Given base '%s' is not a valid commit on '%s'."
                % (self.args[1], self.args[0]))

class TagExistsError(GitflowError): pass

class AlreadyInitialized(GitflowError):
    def __str__(self):
        return ("Already initialized for gitflow.\n"
                "To force reinitialization use: git flow init -f")


class NoSuchLocalBranchError(NoSuchBranchError):
    def __str__(self):
        return ("Local branch '%s' does not exist." % self.args[0])
