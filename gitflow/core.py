from gitflow.repo import get_repo, get_setting

DEFAULT_MASTER_BRANCH = 'master'
DEFAULT_DEVELOP_BRANCH = 'develop'
DEFAULT_ORIGIN_REMOTE = 'origin'

DEFAULT_FEATURE_PREFIX = 'feature/'
DEFAULT_RELEASE_PREFIX = 'release/'
DEFAULT_HOTFIX_PREFIX = 'hotfix/'
DEFAULT_SUPPORT_PREFIX = 'support/'
DEFAULT_VERSIONTAG_PREFIX = ''


class InvalidSpecialBranchException(Exception):
    pass


class SpecialBranch(object):
    def __init__(self, branch):
        supported_types = (
           DEFAULT_FEATURE_PREFIX,
           DEFAULT_RELEASE_PREFIX,
           DEFAULT_HOTFIX_PREFIX,
           DEFAULT_SUPPORT_PREFIX)
        for type_ in supported_types:
            fullname = branch.name
            if fullname.startswith(feature_prefix()):
                self.type = 'feature'
                self.branch = branch
                self.name = fullname[len(feature_prefix()):]
                self.fullname = fullname
                return
        raise InvalidSpecialBranchException('Invalid special branch name.')

    def __str__(self):
        return self.fullname


def master_branchname():
    return get_setting('gitflow.branch.master', DEFAULT_MASTER_BRANCH)


def master_branch():
    return get_repo().heads[master_branchname()]


def develop_branchname():
    return get_setting('gitflow.branch.develop', DEFAULT_DEVELOP_BRANCH)


def develop_branch():
    return get_repo().heads[develop_branchname()]


def origin_remotename():
    return get_setting('gitflow.origin', DEFAULT_ORIGIN_REMOTE)


def feature_prefix():
    return get_setting('gitflow.prefix.feature', DEFAULT_FEATURE_PREFIX)


def release_prefix():
    return get_setting('gitflow.prefix.release', DEFAULT_RELEASE_PREFIX)


def hotfix_prefix():
    return get_setting('gitflow.prefix.hotfix', DEFAULT_HOTFIX_PREFIX)


def support_prefix():
    return get_setting('gitflow.prefix.support', DEFAULT_SUPPORT_PREFIX)


def versiontag_prefix():
    return get_setting('gitflow.prefix.versiontag', DEFAULT_VERSIONTAG_PREFIX)


def branches_with_prefix(prefix):
    fbs = []
    for b in get_repo().branches:
        if b.name.startswith(prefix):
            fbs.append(SpecialBranch(b))
    return fbs


def feature_branches():
    return branches_with_prefix(feature_prefix())
