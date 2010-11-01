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

    def default_base(self):
        return self.gitflow.develop_name()

    def list(self):
        return list(self.iter())

    def iter(self):
        for branch in self.gitflow.repo.branches:
            if branch.name.startswith(self.prefix):
                yield branch

    def create(self, name, base=None):
        repo = self.gitflow.repo

        full_name = self.prefix + name
        if base is None:
            base = self.default_base()
        branch = repo.create_head(full_name, base)
        branch.checkout()
        return branch

    def merge(self, name, into, message=None):
        repo = self.gitflow.repo
        repo.branches[into].checkout()
        full_name = self.prefix + name
        kwargs = dict()
        kwargs['no_ff'] = True
        if not message is None:
            message = message % \
                        dict(name=full_name, identifier=self.identifier)
            kwargs['message'] = message
        repo.git.merge(full_name, **kwargs)

    def delete(self, name, force=False):
        repo = self.gitflow.repo
        full_name = self.prefix + name
        repo.delete_head(full_name, force=force)



class FeatureBranchManager(BranchManager):
    identifier = 'feature'
    prefix = 'feature/'


class ReleaseBranchManager(BranchManager):
    identifier = 'release'
    prefix = 'release/'


class HotfixBranchManager(BranchManager):
    identifier = 'hotfix'
    prefix = 'hotfix/'

    def default_base(self):
        return self.gitflow.master_name()


class SupportBranchManager(BranchManager):
    identifier = 'support'
    prefix = 'support/'


