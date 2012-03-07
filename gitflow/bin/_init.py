# -*- coding: utf-8 ; ispell-local-dictionary: "american" -*-
"""
git-flow init
"""
#
# This file is part of `gitflow`.
# Copyright (c) 2010-2011 Vincent Driessen
# Copyright (c) 2012 Hartmut Goebel
# Distributed under a BSD-like license. For full terms see the file LICENSE.txt
#

import readline # this will trigger readline functionality for raw_input

from gitflow.core import GitFlow as CoreGitFlow, warn

from gitflow.exceptions import (AlreadyInitialized, NotInitialized,
                                NoSuchLocalBranchError, NoSuchBranchError)

__copyright__ = "2010-2011 Vincent Driessen; 2012 Hartmut Goebel"
__license__ = "BSD"

class GitFlow(CoreGitFlow):

    @staticmethod
    def _has_configured(branch_func):
        try:
            branch_func()
        except (NotInitialized, IndexError):
            return False
        return True

    def has_master_configured(self):
        return self._has_configured(self.master)

    def has_develop_configured(self):
        return self._has_configured(self.develop)

    def get_default(self, setting):
        return self.get(setting, self.defaults[setting])
        

def _ask_branch(args, name, desc1, desc2, suggestions, filter=[]):
    # Two cases are distinguished:
    # 1. A fresh git repo (without any branches)
    #    We will create a new master/develop branch for the user
    # 2. Some branches do already exist
    #    We will disallow creation of new master/develop branches and
    #    rather allow to use existing branches for git-flow.
    name = 'gitflow.branch.' + name
    default_name = gitflow.get_default(name)
    local_branches = [b
                      for b in gitflow.branch_names()
                      if b not in filter]
    if not local_branches:
        if not filter:
            print "No branches exist yet. Base branches must be created now."
        should_check_existence = False
        default_suggestion = default_name
    else:
        should_check_existence = True
        print
        print "Which branch should be used for %s?" % desc1
        for b in local_branches:
            print '  -', b
        for default_suggestion in [default_name] + suggestions:
            if default_suggestion in local_branches:
                break
        else:
            default_suggestion = ''

    if args.use_defaults and default_suggestion:
        print "Branch name for %s:" % desc2, default_suggestion
        branch_name = default_suggestion
    else:
        answer = raw_input("Branch name for %s: [%s] "
                           % (desc2, default_suggestion))
        branch_name = answer.strip() or default_suggestion
    if not branch_name:
        raise SystemExit('You need to give a branch name.')
    # check existence in case of an already existing repo
    if branch_name in filter:
        raise SystemExit("Production and integration branches should differ.")
    if should_check_existence:
        # if no local branch exists and a remote branch of the same
        # name exists, checkout that branch and use it for the local branch
        if not branch_name in local_branches:
            remote_name = gitflow.origin_name(branch_name)
            if remote_name in gitflow.branch_names(remote=True):
                gitflow.repo.branch(branch_name, remote_name)
            else:
                raise NoSuchLocalBranchError(branch_name)

    # store the name of the develop branch
    gitflow.set(name, branch_name)
    return branch_name


def _ask_config(args, name, question):
    default_suggestion = gitflow.get_default(name)
    if args.use_defaults:
        print question +':', default_suggestion
        answer = default_suggestion
    else:
        answer = raw_input(question + '? [' + default_suggestion + '] ')
        answer = answer.strip() or default_suggestion
        if answer == '-':
            answer = ''
    gitflow.set(name, answer)

def _ask_prefix(args, name, question):
    name = 'gitflow.prefix.' + name
    if not gitflow.get(name, None) or args.force:
        _ask_config(args, name, question)

def _ask_name(args, name, question):
    name = 'gitflow.' + name
    if not gitflow.get(name, None) or args.force:
        _ask_config(args, name, question)


def run_default(args):
    global gitflow
    gitflow = GitFlow()
    gitflow._enforce_git_repo()

    if gitflow.is_initialized():
        if not args.force:
            raise AlreadyInitialized()

    if args.use_defaults:
        warn("Using default branch names.")

    _ask_name(args, "origin", "Remote name to use as origin in git flow")
 
    #-- add a master branch if no such branch exists yet
    if gitflow.has_master_configured() and not args.force:
        master_branch = gitflow.master_name()
    else:
        master_branch = _ask_branch(args,
            'master',
            'bringing forth production releases',
            'production releases',
            ['production', 'main', 'master'])

    #-- add a develop branch if no such branch exists yet
    if gitflow.has_develop_configured() and not args.force:
        develop_branch = gitflow.develop_name()
    else:
        develop_branch = _ask_branch(args,
            'develop',
            'integration of the "next release"',
            '"next release" development',
            ['develop', 'int', 'integration', 'master'],
            filter=[master_branch])

    if not gitflow.is_initialized() or args.force:
        print
        print "How to name your supporting branch prefixes?"

    _ask_prefix(args, "feature", "Feature branches")
    _ask_prefix(args, "release", "Release branches")
    _ask_prefix(args, "hotfix", "Hotfix branches")
    _ask_prefix(args, "support", "Support branches")
    _ask_prefix(args, "versiontag", "Version tag prefix")

    # assert the gitflow repo has been correctly initialized
    assert gitflow.is_initialized()

    gitflow.init(master_branch, develop_branch)
