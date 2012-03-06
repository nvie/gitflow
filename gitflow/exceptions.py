
class GitflowError(Exception): pass

class NotInitialized(GitflowError): pass
class WorkdirIsDirtyError(GitflowError): pass

class MergeConflict(GitflowError):
    def __str__(self):
        return '\n'.join([
            "Merge conflicts not resolved yet, use:",
            "    git mergetool",
            "    git commit",
            ])

class BranchExists(GitflowError): pass
class BranchExistsError(GitflowError):pass
class NoSuchBranchError(GitflowError):pass

class InvalidOperation(GitflowError): pass

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
