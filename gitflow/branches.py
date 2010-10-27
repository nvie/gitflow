class Branch(object):
    __slots__ = ('prefix', 'name', 'shortname')

    def __init__(self, shortname, prefix=None):
        self.shortname = shortname
        if not prefix is None:
            self.prefix = prefix
        self.name = self.prefix + shortname

    def __str__(self):
        return '<%s.%s "%s">' % (self.__class__.__module__,
                self.__class__.__name__, self.name)


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


