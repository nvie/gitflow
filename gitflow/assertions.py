from gitflow.repo import get_setting, branch_exists
from gitflow.core import master_branchname, develop_branchname


class NotInitializedException(Exception):
    pass


def gitflow_has_master_configured():
    master = master_branchname()
    return master and branch_exists(master)


def gitflow_has_develop_configured():
    develop = develop_branchname()
    return develop and branch_exists(develop)


def gitflow_has_prefixes_configured():
    settings = (
       'gitflow.prefix.feature',
       'gitflow.prefix.release',
       'gitflow.prefix.hotfix',
       'gitflow.prefix.support',
       'gitflow.prefix.versiontag',
    )
    for setting in settings:
        if get_setting(setting) is None:
            return False
    return True


def is_gitflow_initialized():
    return gitflow_has_master_configured() and \
           gitflow_has_develop_configured() and \
           master_branchname() != develop_branchname() and \
           gitflow_has_prefixes_configured()


def require_gitflow_initialized():
    if not is_gitflow_initialized():
        raise NotInitializedException('This repository is not yet enabled for use with git-flow. To initialize this repo, run "git flow init" first.')
