from git import Repo
from ConfigParser import NoSectionError, DuplicateSectionError, \
   NoOptionError, MissingSectionHeaderError, ParsingError

repo = Repo('.')
config = repo.config_reader()


def get_setting(setting, default=None):
    groups = setting.split('.', 2)
    if len(groups) == 2:
        subsection = None
        section, option = groups
    elif len(groups) == 3:
        section, subsection, option = groups
    else:
        raise ValueError('Invalid setting name: %s' % setting)

    try:
        setting = config.get('%s "%s"' % (section, subsection), option)
        return setting
    except (NoSectionError, DuplicateSectionError, NoOptionError,
            MissingSectionHeaderError, ParsingError):
        return default


def branch_exists(branchname):
    for branch in repo.branches:
        if branch.name == branchname:
            return True
    return False
