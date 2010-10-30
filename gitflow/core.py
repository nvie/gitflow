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


class GitFlow(object):
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

    def _init_config(self,
            master=None, develop=None,
            feature=None, release=None, hotfix=None,
            support=None, force_defaults=False):
        defaults = [
            ('gitflow.branch.master', 'master', master),
            ('gitflow.branch.develop', 'develop', develop),
            ('gitflow.prefix.feature', 'feature/', feature),
            ('gitflow.prefix.release', 'release/', release),
            ('gitflow.prefix.hotfix', 'hotfix/', hotfix),
            ('gitflow.prefix.support', 'support/', support),
        ]
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
        

    def init(self,
            master=None, develop=None,
            feature=None, release=None, hotfix=None,
            support=None, force_defaults=False):

        if self.repo is None:
            try:
                self.repo = Repo(self.working_dir)
            except InvalidGitRepositoryError:
                # Git repo is not yet initialized
                self.git.init()

                # Try it again with an inited git repo
                self.repo = Repo(self.working_dir)

        self._init_config(master, develop, feature, release, hotfix, support,
                force_defaults)
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

    def feature_prefix(self):
        return self._safe_get('gitflow.prefix.feature')

    def hotfix_prefix(self):
        return self._safe_get('gitflow.prefix.hotfix')

    def release_prefix(self):
        return self._safe_get('gitflow.prefix.release')

    def support_prefix(self):
        return self._safe_get('gitflow.prefix.support')


    @requires_repo
    def is_dirty(self):
        """
        Returns whether or not the current working directory contains
        uncommitted changes.
        """
        return self.repo.is_dirty()

    def branch_exists(self, name):
        return Head(self.repo, Head.to_full_path(name)).is_valid()

    @requires_repo
    def branch_names(self):
        return map(lambda h: h.name, self.repo.branches)


    @requires_repo
    def status(self):
        result = []
        active_branch = self.repo.active_branch
        for b in self.repo.branches:
            tup = (b.name, b.commit.hexsha, b == active_branch)
            result.append(tup)
        return result


