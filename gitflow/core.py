import time
import datetime
import os
import sys
from functools import wraps
import git
from git import Git, Repo, InvalidGitRepositoryError, RemoteReference
import ConfigParser
from gitflow.branches import BranchManager, BranchTypeExistsError, \
     NoSuchBranchError
from gitflow.util import itersubclasses


def datetime_to_timestamp(d):
    return time.mktime(d.timetuple()) + d.microsecond / 1e6


def requires_repo(f):
    @wraps(f)
    def _inner(self, *args, **kwargs):
        if self.repo is None:
            msg = 'This repo has not yet been initialized for git-flow.'
            raise NotInitialized(msg)
        return f(self, *args, **kwargs)
    return _inner

def info(*texts):
    for txt in texts:
        print txt

def warn(*texts):
    for txt in texts:
        print >> sys.stderr, txt

def die(*texts):
    warn(*texts)
    raise SystemExit(1)


class NotInitialized(Exception):
    pass

class BranchExists(Exception):
    pass

class InvalidOperation(Exception):
    pass

class _NONE:
    pass


class GitFlow(object):
    """
    Creates a :class:`GitFlow` instance.

    :param working_dir:
        The directory where the Git repo is located.  If not specified, the
        current working directory is used.

    When a :class:`GitFlow` class is instantiated, it autodiscovers all
    subclasses of :class:`gitflow.branches.BranchManager`, so there is no
    explicit registration required.
    """

    def _discover_branch_managers(self):
        managers = {}
        for cls in itersubclasses(BranchManager):
            # TODO: Initialize managers with the gitflow branch prefixes
            managers[cls.identifier] = cls(self)
        return managers

    def __init__(self, working_dir='.'):
        # Allow Repos to be passed in instead of strings
        self.repo = None
        if isinstance(working_dir, Repo):
            self.working_dir = working_dir.working_dir
        else:
            self.working_dir = working_dir

        self.git = Git(self.working_dir)
        try:
            self.repo = Repo(self.working_dir)
        except InvalidGitRepositoryError:
            pass

        self.managers = self._discover_branch_managers()
        self.defaults = {
            'gitflow.branch.master': 'master',
            'gitflow.branch.develop': 'develop',
            'gitflow.prefix.versiontag': '',
            'gitflow.origin': 'origin',
            }
        for i in self.managers:
            self.defaults['gitflow.prefix.%s' % i] = self.managers[i].prefix


    def _init_config(self, master=None, develop=None, prefixes={},
                     force_defaults=False):
        for setting, default in self.defaults.items():
            if force_defaults:
                value = default
            elif setting == 'gitflow.branch.master':
                value = master
            elif setting == 'gitflow.branch.develop':
                value = develop
            else:
                prefix = setting[len('gitflow.prefix.'):]
                value = prefixes.get(prefix, None)
            if value is None:
                value = self.get(setting, default)
            self.set(setting, value)

    def _init_initial_commit(self):
        try:
            self.master()
        except IndexError:
            # Create 'master' branch if it does not exist
            info('Creating branch %r' % self.master_name())
            c = self.repo.index.commit('Initial commit', head=False)
            self.repo.create_head(self.master_name(), c)

    def _init_develop_branch(self):
        # NOTE: This function assumes master already exists
        try:
            self.develop()
        except IndexError:
            # Create 'develop' branch if it does not exist
            info('Creating branch %r' % self.develop_name())
            branch = self.repo.create_head(self.develop_name(), self.master())
            # switch to develop branch if its newly created
            info('Switching to branch %s' % branch)
            branch.checkout()

    def _enforce_git_repo(self):
        """
        Ensure a (maybe empty) repository exists we can work on.

        This is to be used by the `init` sub-command.
        """
        if self.repo is None:
            self.git.init(self.working_dir)
            self.repo = Repo(self.working_dir)

    def init(self, master=None, develop=None, prefixes={},
             force_defaults=False):
        self._enforce_git_repo()
        self._init_config(master, develop, prefixes, force_defaults)
        self._init_initial_commit()
        self._init_develop_branch()

    def is_initialized(self):
        return (self.repo and
                self.is_set('gitflow.branch.master') and
                self.is_set('gitflow.branch.develop') and
                self.is_set('gitflow.prefix.feature') and
                self.is_set('gitflow.prefix.release') and
                self.is_set('gitflow.prefix.hotfix') and
                self.is_set('gitflow.prefix.support') and
                self.is_set('gitflow.prefix.versiontag'))

    def _parse_setting(self, setting):
        groups = setting.split('.', 2)
        if len(groups) == 2:
            section, option = groups
        elif len(groups) == 3:
            section, subsection, option = groups
            section = '%s "%s"' % (section, subsection)
        else:
            raise ValueError('Invalid setting name: %s' % setting)
        return (section, option)

    @requires_repo
    def get(self, setting, default=_NONE):
        section, option = self._parse_setting(setting)
        try:
            return self.repo.config_reader().get_value(section, option)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            if default is not _NONE:
                return default
            raise

    @requires_repo
    def set(self, setting, value):
        section, option = self._parse_setting(setting)
        self.repo.config_writer().set_value(section, option, value)

    def is_set(self, setting):
        return self.get(setting, None) is not None


    @requires_repo
    def _safe_get(self, setting_name):
        try:
            return self.get(setting_name)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            raise NotInitialized('This repo has not yet been initialized.')

    def master_name(self):
        return self._safe_get('gitflow.branch.master')

    def develop_name(self):
        return self._safe_get('gitflow.branch.develop')

    def origin_name(self, name=None):
        origin = self.get('gitflow.origin', self.defaults['gitflow.origin'])
        if name is not None:
            return origin + '/' + name
        else:
            return origin

    @requires_repo
    def origin(self):
        return self.repo.branches[self.origin_name()]

    @requires_repo
    def develop(self):
        return self.repo.branches[self.develop_name()]

    @requires_repo
    def master(self):
        return self.repo.branches[self.master_name()]

    def get_prefix(self, identifier):
        return self._safe_get('gitflow.prefix.%s' % (identifier,))


    @requires_repo
    def is_dirty(self):
        """
        Returns whether or not the current working directory contains
        uncommitted changes.
        """
        return self.repo.is_dirty()

    @requires_repo
    def branch_names(self, remote=False):
        if remote:
            return [r.name
                    for r in self.repo.refs
                    if isinstance(r, RemoteReference)]
        else:
            return [r.name for r in self.repo.branches]


    @requires_repo
    def start_transaction(self, message=None):
        if message:
            info(message)

    def name_or_current(self, identifier, prefix):
        """
        If the prefix is empty, see if the current branch is of type
        :param`identifier`. If so, returns the current branches short
        name, otherwise raises :exc:`NoSuchBranchError`.

        If exactly one branch of type :param`identifier` starts with
        the given name prefix, returns that branches short name.
        Raises :exc:`NoSuchBranchError` in case no branch exists with
        the given prefix, or :exc:`PrefixNotUniqueError` in case
        multiple matches are found.
        """
        repo = self.repo
        manager = self.managers[identifier]
        if not prefix:
            if repo.active_branch.name.startswith(manager.prefix):
                return manager.shorten(repo.active_branch.name)
            else:
                raise NoSuchBranchError('The current branch is no %s branch.'
                    'Please specify one explicitly.' % identifier)
        return manager.shorten(manager.by_name_prefix(prefix).name)


    def list(self, identifier, arg0_name, use_tagname, verbose=False):
        repo = self.repo
        manager = self.managers[identifier]
        branches = manager.list()
        if not branches:
            die('',
                'No %s branches exist.' % identifier,
                'You can start a new %s branch with the command:' % identifier,
                '',
                '    git flow %s start <%s> [<base>]' % (identifier, arg0_name),
                '')

        # determine the longest branch name
        width = max(len(b.name) for b in branches) - len(manager.prefix) + 1

        basebranch_sha = repo.branches[manager.default_base()].commit.hexsha

        for branch in branches:
            if repo.active_branch == branch:
                prefix = '* '
            else:
                prefix = '  '

            name = manager.shorten(branch.name)
            extra_info = ''

            if verbose:
                name = name.ljust(width)
                branch_sha = branch.commit.hexsha
                base_sha = repo.git.merge_base(basebranch_sha, branch_sha)
                if branch_sha == basebranch_sha:
                    extra_info = '(no commits yet)'
                elif use_tagname:
                    tagname = self.git.name_rev('--tags','--name-only',
                                                '--no-undefined', base_sha)
                    if not tagname:
                        r.git.rev_parse('--short', base_sha)
                elif base_sha == branch_sha:
                    extra_info = '(is behind develop, may ff)'
                elif base_sha == basebranch_sha:
                    extra_info = '(based on latest develop)'
                else:
                    extra_info = '(may be rebased)'

            info(prefix + name + extra_info)


    def create(self, identifier, name, base, fetch):
        """
        Creates a branch of the given type, with the given short name.

        :param identifier:
            The identifier for the type of branch to create.
            A :class:`BranchManager <git.branches.BranchManager>` for the given
            identifier must exist in the :attr:`self.managers`.

        :param name:
            The friendly (short) name to create.

        :param base:
            The alternative base to branch off from.  If not given, the default
            base for the given branch type is used.

        :returns:
            The newly created :class:`git.refs.Head` branch.
        """
        return self.managers[identifier].create(name, base, fetch=fetch)

    def finish(self, identifier, nameprefix):
        """
        Finishes a branch of the given type, with the given short name.

        :param identifier:
            The identifier for the type of branch to finish.
            A :class:`BranchManager <git.branches.BranchManager>` for the given
            identifier must exist in the :attr:`self.managers`.

        :param name:
            The friendly (short) name to finish.
        """
        mgr = self.managers[identifier]
        branch = mgr.by_name_prefix(nameprefix)
        mgr.finish(mgr.shorten(branch.name))


    def checkout(self, identifier, name):
        mgr = self.managers[identifier]
        branch = mgr.by_name_prefix(name)
        branch.checkout()


    @requires_repo
    def track(self, identifier, name):
        repo = self.repo
        mgr = self.managers[identifier]
        # sanity checks
        # :todo: require_clean_working_tree
        full_name = mgr.full_name(name)
        if full_name in repo.branches:
            raise BranchExistsError(full_name)
        remote_name = self.origin_name(full_name)
        self.origin().fetch(full_name)
        branch = repo.create_head(full_name, remote_name)
        branch.set_tracking_branch(remote_name)
        return branch.checkout()

    @requires_repo
    def publish(self, identifier, name):
        repo = self.repo
        mgr = self.managers[identifier]

        # sanity checks
        # :todo: require_clean_working_tree
        full_name = mgr.full_name(name)
        remote_name = self.origin_name(full_name)
        if not full_name in repo.branches:
            raise NoSuchBranchError(full_name)
        if remote_name in repo.branches:
            raise BranchExistsError(remote_name)

        origin = self.origin()
        # create remote branch
        origin.push('%s:refs/heads/%s' % (branch, branch))
        origin.fetch()

        # configure remote tracking
        self.set ("branch.%s.remote" % branch, origin)
        self.set ("branch.%s.merge" % branch, "refs/heads/%s" % branch)
        return branch.checkout()


    @requires_repo
    def diff(self, identifier, name):
        repo = self.repo
        mgr = self.managers[identifier]
        full_name = mgr.full_name(name)
        base = self.git.merge_base(mgr.default_base(), full_name)
        print self.git.diff('%s..%s' % (base, full_name))


    @requires_repo
    def rebase(self, identifier, name, interactive):
        warn("Will try to rebase %s branch '%s' ..." % (identifier, name))
        repo = self.repo
        mgr = self.managers[identifier]
        full_name = mgr.full_name(name)
        # :todo: require_clean_working_tree
        self.checkout(identifier, name)
        args = []
        if interactive:
            args.append('-i')
        args.append(mgr.default_base())
        self.git.rebase(*args)

    @requires_repo
    def pull(self, identifier, remote, local_name):

        def avoid_accidental_cross_branch_action(branch_name):
            current_branch = repo.active_branch
            if branch_name != current_branch.name:
                warn("Trying to pull from '%s' while currently on branch '%s'."
                     % (branch_name , current_branch))
                raise SystemExit("To avoid unintended merges, git-flow aborted.")

        repo = self.repo
        mgr = self.managers[identifier]
        full_name = mgr.full_name(name)
        # To avoid accidentally merging different feature branches
        # into each other, die if the current feature branch differs
        # from the requested $NAME argument.
        if repo.active_branch.name.startswith(self.get_prefix(identifier)):
            # We are on a local `identifier` branch already, so `full_name`
            # must be equal to the current branch.
            avoid_accidental_cross_branch_action(full_name)
        # :todo: require_clean_working_tree
        if full_name in self.repo.branches:
            # Again, avoid accidental merges
            avoid_accidental_cross_branch_action(full_name)
            # We already have a local branch called like this, so
            # simply pull the remote changes in
            repo.remotes[remote].pull(full_name)
            info("Pulled %s's changes into %s." % (remote_name, fullname))
        else:
            # Setup the local branch clone for the first time
            repo.remotes[remote].fetch(full_name) # stores in FETCH_HEAD
            # set up a non-tracking branch
            branch = repo.create_head(full_name, 'FETCH_HEAD')
            branch.checkout()
            info("Created local branch $s based on %s's $s."
                 % (full_name, remote_name, full_name))


    @requires_repo
    def status(self):
        result = []
        for b in self.repo.branches:
            tup = self.branch_info(b.name)
            result.append(tup)
        return result


    @requires_repo
    def branch_info(self, name):
        active_branch = self.repo.active_branch
        b = self.repo.heads[name]
        return (name, b.commit.hexsha, b == active_branch)


    @requires_repo
    def compare_branches(self, branch1, branch2):
        """
        Tests whether branches and their 'origin' counterparts have
        diverged and need merging first. It returns error codes to
        provide more detail, like so:

        0    Branch heads point to the same commit
        1    First given branch needs fast-forwarding
        2    Second given branch needs fast-forwarding
        3    Branch needs a real merge
        4    There is no merge base, i.e. the branches have no common ancestors
        """
        try:
            commit1 = self.repo.rev_parse(branch1)
            commit2 = self.repo.rev_parse(branch2)
        except git.BadObject, e:
            raise NoSuchBranch(e.args[0])
        if commit1 == commit2:
            return 0
        try:
            base = repo.git.merge_base(commit1, commit2)
        except GitCommandError:
            return 4
        if base == commit1:
            return 1
        elif base == commit2:
            return 2
        else:
            return 3


    @requires_repo
    def require_branches_equal(self, branch1, branch2):
        reop = self.repo
        status = self.compare_branches(branch1, branch2)
        if status == 0:
            # branches are equal
            return
        else:
            warn("Branches '%s' and '%s' have diverged." % (branch1, branch2))
            if status == 1:
                die("And branch '%s' may be fast-forwarded." % branch1)
            elif status == 2:
                # Warn here, since there is no harm in being ahead
                warn("And local branch '%s' is ahead of '%s'." % (branch1, branch2))
            else:
                die("Branches need merging first.")
