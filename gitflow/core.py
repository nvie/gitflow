import time
import datetime
import os
from functools import wraps
from git import Git, Repo, InvalidGitRepositoryError, GitCommandError
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


class NotInitialized(Exception):
    pass

class BranchExists(Exception):
    pass

class InvalidOperation(Exception):
    pass


class Snapshot(object):
    """
    Initializes a new Snapshot instance, used to store/restore data required to
    undo git-flow actions.

    :param gitflow:
        The :class:`GitFlow` instance that this snapshot belongs to.

    :param description:
        A message to describe the snap shot.

    :param snapdate:
        The date to use for this snapshot.  If not given, use the current date.

    :param state:
        A list of (:attr:`head`, :attr:`hexsha`, :attr:`is_active`) tuples
        describing the state.  If not provided, it asks the :class:`GitFlow`
        instance for the state.  Use this explicit parameter when restoring
        a :class:`Snapshot` from disk, for example.

    :param heads:
        A list of heads to store in the :class:`Snapshot`.  If not specified
        explicitly, all branches are snapped.  Only used when :attr:`state` is
        :const:`None`.
    """
    __slots__ = ('gitflow', 'date', 'description', 'state')

    def __init__(self, gitflow, description, snapdate=None, state=None,
            heads=None):
        self.gitflow = gitflow
        self.description = description
        if snapdate is None:
            self.date = datetime.datetime.now()
        else:
            self.date = snapdate

        if state is None:
            if heads is None:
                self.state = self.gitflow.status()
            else:
                # Only store the branches that are explicitly specified.
                self.state = []
                for head in heads:
                    self.state.append(self.gitflow.branch_info(head))
        else:
            self.state = state

    def __hash__(self, other):
        return hash(self.gitflow) ^ hash(self.date) ^ \
                hash(self.description) ^ hash(self.state)

    def __eq__(self, other):
        """
        Compares this :class:`Snapshot` instance to the instance in
        :attr:`other`.

        :param other:
            The :class:`Snapshot` instance to compare to.
        """
        return self.gitflow == other.gitflow and \
                self.date == other.date and \
                self.description == other.description and \
                set(self.state) == set(other.state)


    def write(self, config, index):
        """
        Write this :class:`Snapshot` instance to the :class:`ConfigParser`
        instance given in :attr:`config`.

        :param config:
            The :class:`ConfigParser` instance to write to.

        :param index:
            The index position of this snapshot in the snapshot stack.  The
            calling object (typically :class:`GitFlow`) is responsible for
            providing the index number this instance should write itself under.
        """
        section = 'meta%d' % index
        heads_section = 'heads%d' % index
        config.add_section(section)
        config.add_section(heads_section)
        config.set(section, 'description', self.description)
        config.set(section, 'date', repr(datetime_to_timestamp(self.date)))
        active = None
        for name, hexsha, is_active in self.state:
            config.set(heads_section, name, hexsha)
            if is_active:
                active = name
        if active:
            config.set(section, 'active', active)

    @classmethod
    def read(self, gitflow, config, index):
        """
        Create a new :class:`Snapshot` instance by reading it from the
        :class:`ConfigParser` (at index :attr:`index`).

        :param gitflow:
            The :class:`GitFlow` instance to register the :class:`Snapshot`
            under.

        :param config:
            The :class:`ConfigParser` instance to read from.

        :param index:
            The index position of this snapshot in the snapshot stack.  The
            calling object (typically :class:`GitFlow`) is responsible for
            providing the index number this instance should write itself under.
        """
        meta = 'meta%d' % index
        heads = 'heads%d' % index

        description = config.get(meta, 'description')
        snapdate = datetime.datetime.fromtimestamp(float(config.get(meta, 'date')))
        active = config.get(meta, 'active')
        state = []
        for name, hexsha in config.items(heads):
            tup = (name, hexsha, active == name)
            state.append(tup)

        snapshot = Snapshot(gitflow, description, snapdate, state)
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
        self._snapshots = None

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
            self.repo.create_head(develop_name, self.master_name())
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


    def snapshots(self):
        """
        Returns the snapshot stack.

        The contents will be read from disk upon first access and will be cached
        for all further access.
        """
        if self._snapshots is None:
            self._snapshots = self._read_snapshots()
        return self._snapshots

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


    def _read_snapshots(self):
        git_dir = self.repo.git_dir
        path = os.path.join(git_dir, 'snapshots')
        if not os.path.exists(path):
            # That's fine, there are not snapshots yet
            return []

        config = ConfigParser.ConfigParser()
        config.read(path)
        num = int(config.get('snapshots', 'num'))
        snapshots = []
        for index in range(num):
            snap = Snapshot.read(self, config, index)
            snapshots.append(snap)
        return snapshots

    def _store_snapshots(self):
        git_dir = self.repo.git_dir
        path = os.path.join(git_dir, 'snapshots')
        config = ConfigParser.ConfigParser()
        config.add_section('snapshots')
        config.set('snapshots', 'num', repr(len(self.snapshots())))

        for index, snapshot in enumerate(self.snapshots()):
            snapshot.write(config, index)

        f = open(path, 'wb')
        try:
            config.write(f)
        finally:
            f.close()

    def snap(self, description, heads=None):
        """
        Make a snapshot of the current state of the repository, push it on the
        snapshot stack, and write it to disk.

        :param description:
            The description to use for this snapshot.

        :param heads:
            A list of heads to store in the snapshot.  If not specified
            explicitly, all branches are snapped.
        """
        snapshot = Snapshot(self, description, heads=heads)
        self.snapshots().append(snapshot)
        self._store_snapshots()
        return snapshot


    def restore(self, snap, backup=True):
        """
        Restores the state of the current repository to the state captured in
        the snapshot.

        :param snap:
            The :class:`Snapshot` instance representing the state to restore the
            current repository to.

        :param backup:
            If :const:`True`, the references to the current heads are kept
            around in special `backup/` branches, so no objects will be
            discarded during the next garbage collection.
        """
        for name, hexsha, is_active in snap.state:
            if backup:
                self.repo.create_head('backup/' + name, commit=name)
            if name == self.repo.active_branch.name:
                # reset --hard :)
                self.repo.head.reset(hexsha, index=True, working_tree=True)
            else:
                self.repo.create_head(name, commit=hexsha, force=True)
            #print name, hexsha, '* '[not is_active]


