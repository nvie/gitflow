class Branch(object):
    __slots__ = ('gitflow', 'prefix', 'name', 'fullname')

    def __init__(self, gitflow, name, prefix=None):
        self.gitflow = gitflow
        self.name = name
        if not prefix is None:
            self.prefix = prefix
        self.fullname = self.prefix + name


class FeatureBranch(Branch):
    identifier = 'feature'
    prefix = 'feature/'


class ReleaseBranch(Branch):
    identifier = 'release'
    prefix = 'release/'


class HotfixBranch(Branch):
    identifier = 'hotfix'
    prefix = 'hotfix/'


class SupportBranch(Branch):
    identifier = 'support'
    prefix = 'support/'


