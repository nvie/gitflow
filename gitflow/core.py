import time
import datetime
import os
import sys
from functools import wraps
from git import Git, Repo, InvalidGitRepositoryError, RemoteReference
import ConfigParser
from gitflow.branches import BranchManager
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
                value = prefixes.get(setting, None)
            if value is None or not self.is_set(setting):
                value = default
            self.set(setting, value)


    def _init_initial_commit(self):
        try:
            self.master()
        except IndexError:
            # Create 'master' branch if it does not exist
            print('Creating branch %r' % self.master_name())
            c = self.repo.index.commit('Initial commit', head=False)
            self.repo.create_head(self.master_name(), c)

    def _init_develop_branch(self):
        # NOTE: This function assumes master already exists
        try:
            self.develop()
        except IndexError:
            # Create 'develop' branch if it does not exist
            print('Creating branch %r' % self.develop_name())
            branch = self.repo.create_head(self.develop_name(), self.master())
            # switch to develop branch if its newly created
            print('Switching to branch %s' % branch)
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
    def get(self, setting, null=False):
        section, option = self._parse_setting(setting)
        try:
            return self.repo.config_reader().get_value(section, option)
        except:
            if null:
                return None
            raise

    @requires_repo
    def set(self, setting, value):
        section, option = self._parse_setting(setting)
        self.repo.config_writer().set_value(section, option, value)

    def is_set(self, setting):
        return not self.get(setting, null=True) is None


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
        return map(lambda h: h.name, self.repo.branches)


    def create(self, identifier, name, base=None):
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
        return self.managers[identifier].create(name, base)

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


