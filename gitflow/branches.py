from git import GitCommandError


class BranchManager(object):
    """
    Initializes an instance of :class:`BranchManager`.  A branch
    manager is responsible for listing, creating, merging, deleting,
    finishing (i.e. merging+deleting) branches of a given type.

    :param gitflow:
        The :class:`gitflow.core.GitFlow` instance that this branch
        manager belongs to.

    :param prefix:
        The prefix to use for the type of branches that this branch
        manager manages.
    """

    def __init__(self, gitflow, prefix=None):
        from gitflow.core import GitFlow
        assert isinstance(gitflow, GitFlow), 'Argument \'gitflow\' must be a GitFlow instance.'
        self.gitflow = gitflow
        if not prefix is None:
            assert isinstance(prefix, basestring), 'Argument \'prefix\' must be a string.'
            self.prefix = prefix

    def default_base(self):
        """
        Returns the name of branch to use as the default base for branching off
        from in case no explicit base is specified.

        This method can be overriden in a subclass of :class:`BranchManager`.
        If not overriden, the default is to use the "develop" branch.
        """
        return self.gitflow.develop_name()

    def list(self):
        """
        Returns a list of all branches of the type that this manager
        manages.  See also :meth:`iter`.
        """
        return list(self.iter())

    def iter(self):
        """
        Returns an iterator, iterating over all branches of the type that
        this manager manages.
        """
        for branch in self.gitflow.repo.branches:
            if branch.name.startswith(self.prefix):
                yield branch

    def create(self, name, base=None):
        """
        Creates a branch of the type that this manager manages and checks it
        out.

        :param name:
            The (short) name of the branch to create.

        :param base:
            The base commit or ref to base the branch off from.  If a base is
            not provided explicitly, the default base for this type of branch is
            used.  See also :meth:`default_base`.
        """
        repo = self.gitflow.repo

        full_name = self.prefix + name
        if base is None:
            base = self.default_base()
        branch = repo.create_head(full_name, base)
        branch.checkout()
        return branch

    def _is_single_commit_branch(self, from_, to):
        git = self.gitflow.repo.git
        commits = git.rev_list('%s...%s' % (from_, to), n=2).split()
        return len(commits) == 1

    def merge(self, name, into, message=None):
        """
        This merges the branch named :attr:`name` into the branch named
        :attr:`into`, using commit message :attr:`message`.

        :param name:
            The name of the branch that needs merging.
        :param into:
            The name of the branch to merge into.
        :param message:
            The commit message to use for the merge commit.  If it is not given,
            a default merge message is used.  You can use the following string
            placeholders, which :meth:`merge` will expand::

                %(name)s = The full name of the branch (e.g. "feature/foo")
                %(short_name)s = The friendly name of the branch (e.g. "foo")
                %(identifier)s = The type (e.g. "feature", "hotfix", etc.)

        You typically don't need to override this method in a subclass.
        """
        repo = self.gitflow.repo
        repo.branches[into].checkout()
        full_name = self.prefix + name

        kwargs = dict()
        if not self._is_single_commit_branch(into, full_name):
            kwargs['no_ff'] = True
        if not message is None:
            message = message % \
                        dict(name=full_name, identifier=self.identifier,
                                short_name=name)
            kwargs['message'] = message
        repo.git.merge(full_name, **kwargs)

    def delete(self, name, force=False):
        """
        This deletes a branch of the type that this manager manages named
        :attr:`name`.

        :param name:
            The (short) name of the branch to delete.

        :param force:
            Delete the branch, even if this would lead to data loss.
        """
        repo = self.gitflow.repo
        full_name = self.prefix + name
        repo.delete_head(full_name, force=force)

    def finish(self, name):
        """
        Finishes the branch of the type that this manager manages named
        :attr:`name`.  Finishing means that:

        * The branch is merged into all branches that require it to be merged
          in to.  The model prescribes the branching/merging rules for each
          branch type, so this depends on the implementing subclass.
        * The branch is deleted if all merges are successful.

        :param name:
            The (short) name of the branch to finish.
        """
        self.merge(name, self.gitflow.develop_name(),
                'Finished %(identifier)s %(short_name)s.')
        self.delete(name)

    def shorten(self, full_name):
        """
        Returns the friendly (short) name of this branch, without the prefix,
        given the fully qualified branch name.

        :param full_name:
            The full name of the branch as it is known to Git, including the
            prefix.

        :returns:
            The friendly name of the branch.
        """
        if full_name.startswith(self.prefix):
            return full_name[len(self.prefix):]
        else:
            return full_name


class FeatureBranchManager(BranchManager):
    identifier = 'feature'
    prefix = 'feature/'


class ReleaseBranchManager(BranchManager):
    identifier = 'release'
    prefix = 'release/'

    def finish(self, name):
        self.merge(name, self.gitflow.master_name(),
                'Finished %(identifier)s %(short_name)s.')
        self.merge(name, self.gitflow.develop_name(),
                'Finished %(identifier)s %(short_name)s.')
        self.delete(name)


class HotfixBranchManager(BranchManager):
    identifier = 'hotfix'
    prefix = 'hotfix/'

    def default_base(self):
        return self.gitflow.master_name()

    def finish(self, name):
        self.merge(name, self.gitflow.master_name(),
                'Finished %(identifier)s %(short_name)s.')
        self.merge(name, self.gitflow.develop_name(),
                'Finished %(identifier)s %(short_name)s.')
        self.delete(name)


class SupportBranchManager(BranchManager):
    identifier = 'support'
    prefix = 'support/'

    def default_base(self):
        return self.gitflow.master_name()

    def finish(self, name):
        raise NotImplementedError("Finishing support branches does not make "
                "any sense.")

