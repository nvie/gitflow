from config import Config
from git import Repo
from ConfigParser import NoOptionError, NoSectionError, DuplicateSectionError, \
                         MissingSectionHeaderError, ParsingError


class NotInitialized(Exception):
    pass


class GitFlow(object):
    def __init__(self, repo):
        self.repo = repo
        self.config = Config(repo)

    def init(self,
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
                if force_defaults or self.get(setting, null=True) is None:
                    self.set(setting, default)

    def is_initialized(self):
        return self.get('gitflow.branch.master', null=True) \
           and self.get('gitflow.branch.develop', null=True) \
           and self.get('gitflow.prefix.feature', null=True) \
           and self.get('gitflow.prefix.release', null=True) \
           and self.get('gitflow.prefix.hotfix', null=True) \
           and self.get('gitflow.prefix.support', null=True)

    def get(self, setting, default=None, null=False):
        groups = setting.split('.', 2)
        if len(groups) == 2:
            subsection = None
            section, option = groups
        elif len(groups) == 3:
            section, subsection, option = groups
        else:
            raise ValueError('Invalid setting name: %s' % setting)

        try:
            if subsection:
                lookup_key = '%s "%s"' % (section, subsection)
            else:
                lookup_key = section
            setting = self.repo.config_reader().get(lookup_key, option)
            return setting
        except (NoSectionError, DuplicateSectionError, NoOptionError,
                MissingSectionHeaderError, ParsingError):
            if null:
                return None
            elif not default is None:
                return default
            raise

    def set(self, setting, value):
        groups = setting.split('.', 2)
        if len(groups) == 2:
            subsection = None
            section, option = groups
        elif len(groups) == 3:
            section, subsection, option = groups
        else:
            raise ValueError('Invalid setting name: %s' % setting)

        if subsection:
            lookup_key = '%s "%s"' % (section, subsection)
        else:
            lookup_key = section

        writer = self.repo.config_writer()
        if not lookup_key in writer.sections():
            writer.add_section(lookup_key)
        writer.set(lookup_key, option, value)


    def _safe_get(self, setting_name):
        try:
            return self.get(setting_name)
        except NoSectionError, NoOptionError:
            raise NotInitialized('This repo has not yet been initialized.')

    def master(self):
        return self._safe_get('gitflow.branch.master')

    def develop(self):
        return self._safe_get('gitflow.branch.develop')

    def feature_prefix(self):
        return self._safe_get('gitflow.prefix.feature')

    def hotfix_prefix(self):
        return self._safe_get('gitflow.prefix.hotfix')

    def release_prefix(self):
        return self._safe_get('gitflow.prefix.release')

    def support_prefix(self):
        return self._safe_get('gitflow.prefix.support')

