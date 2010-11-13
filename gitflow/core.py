import datetime
import os
try:
    import cPickle as pickle
except ImportError:
    import pickle
from functools import wraps
from git import Git, Repo, Head, InvalidGitRepositoryError, GitCommandError
from ConfigParser import NoOptionError, NoSectionError
from gitflow.branches import BranchManager
from gitflow.util import itersubclasses


def requires_repo(f):
    @wraps(f)
    def _inner(self, *args, **kwargs):
        if self.repo is None:
            msg = 'This repo has not yet been initialized for git-flow.'
            raise NotInitialized(msg)
        return f(self, *args, **kwargs)
    return _inner


class NotInitialized(Exception):
    pass

class BranchExists(Exception):
    pass

class InvalidOperation(Exception):
    pass


class Snapshot(object):
    __slots__ = ('gitflow', 'date', 'description', 'state')

    def __init__(self, gitflow, snapdate, description):
        self.gitflow = gitflow
        self.date = snapdate
        self.description = description
        self.state = self.gitflow.status()

    @classmethod
    def snap(cls, gitflow, description, snapdate=None):
        if snapdate is None:
            snapdate = datetime.datetime.now()
        snapshot = Snapshot(gitflow, snapdate, description)
        snapshot.write()
        return Snapshot


    def __hash__(self, other):
        return hash(self.gitflow) ^ hash(self.date) ^ \
                hash(self.description) ^ hash(self.state)

    def __eq__(self, other):
        return self.gitflow == other.gitflow and \
                self.date == other.date and \
                self.description == other.description and \
                self.state == other.state


    def __getstate__(self):
        return dict(date=self.date,
                description=self.description,
                state=self.state,
                gitflow=None)

    def __setstate__(self, obj):
        self.date = obj['date']
        self.description = obj['description']
        self.state = obj['state']
        self.gitflow = None

    def write(self, writeable):
        pickle.dump(self, writeable)

    @classmethod
    def read(self, gitflow, readable):
        snapshot = pickle.load(readable)
        snapshot.gitflow = gitflow
        return snapshot


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

    def _init_config(self, master=None, develop=None, prefixes={}, force_defaults=False):
        defaults = [
            ('gitflow.branch.master', 'master', master),
            ('gitflow.branch.develop', 'develop', develop),
        ]
        defaults += [('gitflow.prefix.%s' % i, self.managers[i].prefix,
                        prefixes.get(i, None))
                     for i in self.managers]
        for setting, default, value in defaults:
            if not value is None:
                self.set(setting, value)
            else:
                if force_defaults or not self.is_set(setting):
                    self.set(setting, default)

    def _init_initial_commit(self):
        master = self.master_name()
        try:
            self.repo.branches[master]
        except:
            # Only if 'master' branch does not exist
            c = self.repo.index.commit('Initial commit', head=False)
            self.repo.create_head(master, c)

    def _init_develop_branch(self):
        # NOTE: This function assumes master already exists
        develop_name = self.develop_name()
        try:
            self.repo.create_head(self.develop_name(), self.master_name())
        except GitCommandError:
            # on error, the branch existed already
            pass
        

    def init(self, master=None, develop=None, prefixes={}, force_defaults=False):
        if self.repo is None:
            try:
                self.repo = Repo(self.working_dir)
            except InvalidGitRepositoryError:
                # Git repo is not yet initialized
                self.git.init()

                # Try it again with an inited git repo
                self.repo = Repo(self.working_dir)

        self._init_config(master, develop, prefixes, force_defaults)
        self._init_initial_commit()
        self._init_develop_branch()

    def is_initialized(self):
        return self.is_set('gitflow.branch.master') \
           and self.is_set('gitflow.branch.develop') \
           and self.is_set('gitflow.prefix.feature') \
           and self.is_set('gitflow.prefix.release') \
           and self.is_set('gitflow.prefix.hotfix') \
           and self.is_set('gitflow.prefix.support')

    def _parse_setting(self, setting):
        groups = setting.split('.', 2)
        if len(groups) == 2:
            subsection = None
            section, option = groups
        elif len(groups) == 3:
            section, subsection, option = groups
        else:
            raise ValueError('Invalid setting name: %s' % setting)

        if subsection:
            section = '%s "%s"' % (section, subsection)
        else:
            section = section

        return (section, option)

    @requires_repo
    def get(self, setting, null=False):
        section, option = self._parse_setting(setting)
        try:
            setting = self.repo.config_reader().get_value(section, option)
            return setting
        except Exception:
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
        except (NoSectionError, NoOptionError):
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
    def branch_names(self):
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
        active_branch = self.repo.active_branch
        for b in self.repo.branches:
            tup = (b.name, b.commit.hexsha, b == active_branch)
            result.append(tup)
        return result


    @requires_repo
    def make_snapshot(self):
        import simplejson
        status = self.status()
        simplejson.dumps(status)

    @requires_repo
    def start_transaction(self):
        make_snapshot()


