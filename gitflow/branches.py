from git import GitCommandError


class BranchManager(object):
    __slots__ = ('gitflow', 'prefix')

    def __init__(self, gitflow, prefix=None):
        from gitflow.core import GitFlow
        assert isinstance(gitflow, GitFlow), 'Argument \'gitflow\' must be a GitFlow instance.'
        self.gitflow = gitflow
        if not prefix is None:
            assert isinstance(prefix, basestring), 'Argument \'prefix\' must be a string.'
            self.prefix = prefix

    def list(self):
        return list(self.iter())

    def iter(self):
        for branch in self.gitflow.repo.branches:
            if branch.name.startswith(self.prefix):
                yield branch

    def create(self, name):
        repo = self.gitflow.repo

        full_name = self.prefix + name
        base = self.gitflow.develop_name()
        branch = repo.create_head(full_name, base)
        branch.checkout()
        return branch



class FeatureBranchManager(BranchManager):
    identifier = 'feature'
    prefix = 'feature/'


class ReleaseBranchManager(BranchManager):
    identifier = 'release'
    prefix = 'release/'


class HotfixBranchManager(BranchManager):
    identifier = 'hotfix'
    prefix = 'hotfix/'


class SupportBranchManager(BranchManager):
    identifier = 'support'
    prefix = 'support/'


