
class NoSuchBranchError(Exception):
    pass

class BranchExistsError(Exception):
    pass

class PrefixNotUniqueError(Exception):
    pass

class BaseNotOnBranch(Exception):
    def __str__(self):
        return ("Given base '%s' is not a valid commit on '%s'."
                % (self.args[1], self.args[0]))

class WorkdirIsDirtyError(Exception): pass
class BranchTypeExistsError(Exception): pass
class TagExistsError(Exception): pass


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
        manager manages. If this is not `None`, it supersedes the
        configuration of the `gitflow` object's repository.
    """

    def _get_prefix(self):
        if self._prefix is not None:
            return self._prefix
        try:
            return self.gitflow.get_prefix(self.identifier)
        except:
            return self.DEFAULT_PREFIX
    def _set_prefix(self, value): self._prefix = value
    prefix = property(_get_prefix, _set_prefix)

    def __init__(self, gitflow, prefix=None):
        from gitflow.core import GitFlow
        assert isinstance(gitflow, GitFlow), "Argument 'gitflow' must be a GitFlow instance."
        self.gitflow = gitflow
        if not prefix is None:
            assert isinstance(prefix, basestring), "Argument 'prefix' must be a string."
            self.prefix = prefix
        else:
            self.prefix = None

    def default_base(self):
        """
        :returns:
            The name of branch to use as the default base for branching off from
            in case no explicit base is specified.

        This method can be overriden in a subclass of :class:`BranchManager`.
        If not overriden, the default is to use the 'develop' branch.
        """
        return self.gitflow.develop_name()

    def full_name(self, name):
        return self.prefix + name

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

    def by_name_prefix(self, nameprefix):
        """
        If exactly one branch of the type that this manager manages starts with
        the given name prefix, returns that branch.  Raises
        :exc:`NoSuchBranchError` in case no branches exist with the given
        prefix, or :exc:`PrefixNotUniqueError` in case multiple matches are
        found.

        :param nameprefix:
            The name prefix (or full name) of the short branch name to match.

        :returns:
            The :class:`git.refs.Head` instance of the branch that can be
            uniquely identified by the given name prefix.
        """
        nameprefix = self.full_name(nameprefix)
        matches = [b
                   for b in self.iter()
                   if b.name.startswith(nameprefix)]
        num_matches = len(matches)
        if num_matches == 1:
            return matches[0]
        elif num_matches < 1:
            raise NoSuchBranchError('There is no %s branch matching the '
                    'prefix "%s"' % (self.identifier, nameprefix))
        else:
            raise PrefixNotUniqueError('There are multiple %s branches '
                    'matching the prefix "%s": %s' % (self.identifier,
                        nameprefix, matches))

    def iter(self):
        """
        :returns:
            An iterator, iterating over all branches of the type that this
            manager manages.
        """
        for branch in self.gitflow.repo.branches:
            if branch.name.startswith(self.prefix):
                yield branch

    def list(self):
        """
        :returns:
            A list of all branches of the type that this manager manages.  See
            also :meth:`iter`.
        """
        return list(self.iter())

    def create(self, name, base=None, fetch=False,
               must_be_on_default_base=False):
        """
        Creates a branch of the type that this manager manages and checks it
        out.

        :param name:
            The (short) name of the branch to create.

        :param base:
            The base commit or ref to base the branch off from.  If a base is
            not provided explicitly, the default base for this type of branch is
            used.  See also :meth:`default_base`.

        :param fetch:
            If set, update the local repo with remote changes prior to
            creating the new branch.

        :param must_be_on_default_base:
            If set, the `base` must be a valid commit on the branch
            manager `default_base`.

        :returns:
            The newly created :class:`git.refs.Head` reference.
        """
        gitflow = self.gitflow
        repo = gitflow.repo

        full_name = self.prefix + name
        if full_name in repo.branches:
            raise BranchExistsError(full_name)

        origin = None
        if gitflow.origin_name(full_name) in repo.refs:
            # If the origin branch counterpart exists use it
            origin = repo.refs[gitflow.origin_name(full_name)]
        if base is None:
            base = origin and origin.name or self.default_base()
        if must_be_on_default_base:
            if not gitflow.is_merged_into(base, self.default_base()):
                raise BaseNotOnDefaultBranch(self.identifier, self.default_base())

        if gitflow.is_dirty() and not gitflow.has_unmerged_changes():
            raise WorkdirIsDirtyError()

        # update the local repo with remote changes, if asked
        if origin and fetch:
            repo.fetch(origin)

        # If the origin branch counterpart exists, assert that the
        # local branch isn't behind it (to avoid unnecessary rebasing).
        if origin:
            gitflow.require_branches_equal(base, origin.name)

        branch = repo.create_head(full_name, base)
        branch.checkout()
        if origin:
            branch.set_tracking_branch(origin)
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

                %(name)s = The full name of the branch (e.g. 'feature/foo')
                %(short_name)s = The friendly name of the branch (e.g. 'foo')
                %(identifier)s = The type (e.g. 'feature', 'hotfix', etc.)

        You typically don't need to override this method in a subclass.
        """
        full_name = self.prefix + name
        if self.gitflow.is_merged_into(full_name, into):
            # already merged, nothing more to do
            return
        repo = self.gitflow.repo
        repo.branches[into].checkout()

        kwargs = dict()
        if not self._is_single_commit_branch(into, full_name):
            kwargs['no_ff'] = True
        if message is not None:
            message = (message
                       % dict(name=full_name, identifier=self.identifier,
                              short_name=name))
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


class FeatureBranchManager(BranchManager):
    identifier = 'feature'
    DEFAULT_PREFIX = 'feature/'

    def create(self, name, base=None, fetch=False):
        """
        Creates a branch of type `feature` and checks it out.

        :param name:
            The (short) name of the branch to create. This will be
            prefixed by `feature/` or whatever is configured in
            `gitflow.prefix.feature`.

        :param base:
            The base commit or ref to base the branch off from.  If no
            base is provided, it defaults to the branch configured in
            `gitflow.branch.develop`.  See also :meth:`default_base`.

        :param fetch:
            If set, update the local repo with remote changes prior to
            creating the new branch.

        :returns:
            The newly created :class:`git.refs.Head` reference.
        """
        return super(FeatureBranchManager, self).create(
            name, base, fetch=fetch, must_be_on_default_base=False)


    def finish(self, name, fetch=False, rebase=False, keep=False,
               force_delete=False, push=False):
        """
        Finishes the branch of type `feature` named :attr:`name`.
        Finishing means that:

        * The `feature`-branch is merged into the `develop`-branch.
        * The `feature`-branch is deleted if all merges are successful.

        :param name:
            The (short) name of the branch to finish.
        :param fetch:
            If set, update the local repo with remote changes prior to
            merging.
        :param rebase:
            Rebase `featuer`-branch prior to merging.
        :param keep:
            Keep `feature`-branch after performing finish.
        :param force_delete:
            Force deleting the `feature`-branch even if merging failed.
        :param push:
            Push changes to the remote repository.
        """
        gitflow = self.gitflow
        full_name = self.full_name(name)
        gitflow.must_be_uptodate(full_name, fetch=fetch)
        gitflow.must_be_uptodate(gitflow.develop_name(), fetch=fetch)
        if rebase:
            gitflow.rebase(self.identifier, name, interactive=False)
        self.merge(name, self.gitflow.develop_name(),
                   'Finished %(identifier)s %(short_name)s.')
        if not keep:
            self.delete(name, force=force_delete)
        if push:
            gitflow.origin().push(self.gitflow.develop_name())
            if not keep:
                gitflow.origin().push(':'+full_name)


class ReleaseBranchManager(BranchManager):
    identifier = 'release'
    DEFAULT_PREFIX = 'release/'

    def create(self, version, base=None, fetch=False):
        """
        Creates a branch of type `release` and checks it out.

        :param version:
            The version to be released and for which to create the
            release-branch for. This will be prefixed by `release/`
            or whatever is configured in `gitflow.prefix.release`.

        :param base:
            The base commit or ref to base the branch off from.  If no
            base is provided, it defaults to the branch configured in
            `gitflow.branch.develop`.  See also :meth:`default_base`.

        :param fetch:
            If set, update the local repo with remote changes prior to
            creating the new branch.

        :returns:
            The newly created :class:`git.refs.Head` reference.
        """
        # there must be no active `release` branch
        if len(self.list()) > 0:
            raise BranchTypeExistsError(self.identifier)
        # there must be no tag for this version yet
        tagname = self.gitflow.get('gitflow.prefix.versiontag') + version
        if tagname in self.gitflow.repo.tags:
            raise TagExistsError(tagname)
        return super(ReleaseBranchManager, self).create(
            version, base, fetch=fetch, must_be_on_default_base=True)

    def finish(self, name):
        self.merge(name, self.gitflow.master_name(),
                'Finished %(identifier)s %(short_name)s.')
        self.merge(name, self.gitflow.develop_name(),
                'Finished %(identifier)s %(short_name)s.')
        self.delete(name)


class HotfixBranchManager(BranchManager):
    identifier = 'hotfix'
    DEFAULT_PREFIX = 'hotfix/'

    def default_base(self):
        return self.gitflow.master_name()

    def create(self, version, base=None, fetch=False):
        """
        Creates a branch of type `hotfix` and checks it out.

        :param version:
            The version the hotfix will get and for which to create
            the release-branch for. This will be prefixed by `hotfix/`
            or whatever is configured in `gitflow.prefix.hotfix`.

        :param base:
            The base commit or ref to base the branch off from.  If no
            base is provided, it defaults to the branch configured in
            `gitflow.branch.master`.  See also :meth:`default_base`.

        :param fetch:
            If set, update the local repo with remote changes prior to
            creating the new branch.

        :returns:
            The newly created :class:`git.refs.Head` reference.
        """
        # there must be no active `hotfix` branch
        if len(self.list()) > 0:
            raise BranchTypeExistsError(self.identifier)
        # there must be no tag for this version yet
        tagname = self.gitflow.get('gitflow.prefix.versiontag') + version
        if tagname in self.gitflow.repo.tags:
            raise TagExists(tagname)
        return super(HotfixBranchManager, self).create(
            version, base, fetch=fetch, must_be_on_default_base=True)

    def finish(self, name):
        self.merge(name, self.gitflow.master_name(),
                'Finished %(identifier)s %(short_name)s.')
        self.merge(name, self.gitflow.develop_name(),
                'Finished %(identifier)s %(short_name)s.')
        self.delete(name)


class SupportBranchManager(BranchManager):
    identifier = 'support'
    DEFAULT_PREFIX = 'support/'

    def default_base(self):
        return self.gitflow.master_name()

    def create(self, name, base=None, fetch=False):
        """
        Creates a branch of type `support` and checks it out.

        :param name:
            The (short) name of the branch to create. This will be
            prefixed by `support/` or whatever is configured in
            `gitflow.prefix.support`.

        :param base:
            The base commit or ref to base the branch off from.  If no
            base is provided, it defaults to the branch configured in
            `gitflow.branch.develop`.  See also :meth:`default_base`.

        :param fetch:
            If set, update the local repo with remote changes prior to
            creating the new branch.

        :returns:
            The newly created :class:`git.refs.Head` reference.
        """
        return super(SupportBranchManager, self).create(
            name, base, fetch=fetch, must_be_on_default_base=True)

    def finish(self, name):
        raise NotImplementedError("Finishing support branches does not make "
                "any sense.")
