from git import Repo
from ConfigParser import NoOptionError, NoSectionError, DuplicateSectionError, \
                         MissingSectionHeaderError, ParsingError


class Config(object):

    def __init__(self, dot_git=None):
        self.repo = Repo(dot_git)

    def get(self, setting, default=None):
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
            if not default is None:
                return default
            raise


    def _get_branch_name(self, easy_name):
        return self.get('gitflow.branch.%s' % easy_name, easy_name)

    def _get_prefix_name(self, easy_name):
        return self.get('gitflow.prefix.%s' % easy_name, easy_name + '/')

    def master(self):
        return self._get_branch_name('master')

    def develop(self):
        return self._get_branch_name('develop')

    def hotfix_prefix(self):
        return self._get_prefix_name('hotfix')

    def release_prefix(self):
        return self._get_prefix_name('release')

    def support_prefix(self):
        return self._get_prefix_name('support')
