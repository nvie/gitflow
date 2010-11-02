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

    def is_single_commit_branch(self, from_, to):
        git = self.gitflow.repo.git
        commits = git.rev_list('%s...%s' % (from_, to), n=2).split()
        return len(commits) == 1

    def merge(self, name, into, message=None):
        """
        This merges the branch named :name: into the branch named :into:, using
        commit message :message:.  If :message: is not given, a default merge
        message is used.  If :message: is given, you can use the following
        string placeholders, which merge will expand:

        %(name)s       = The full name of the branch, including the prefix
        %(short_name)s = The friendly name of the branch, without prefix
        %(identifier)s = The kind of branch
        """
        repo = self.gitflow.repo
        repo.branches[into].checkout()
        full_name = self.prefix + name

        kwargs = dict()
        if not self.is_single_commit_branch(into, full_name):
            kwargs['no_ff'] = True
        if not message is None:
            message = message % \
                        dict(name=full_name, identifier=self.identifier,
                                short_name=name)
            kwargs['message'] = message
        repo.git.merge(full_name, **kwargs)

    def delete(self, name, force=False):
        repo = self.gitflow.repo
        full_name = self.prefix + name
        repo.delete_head(full_name, force=force)

    def finish(self, name):
        self.merge(name, self.gitflow.develop_name(),
                'Finished %(identifier)s %(short_name)s.')
        self.delete(name)


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


