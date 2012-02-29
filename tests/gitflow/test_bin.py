import sys
from functools import wraps
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from unittest2 import TestCase

import gitflow
from gitflow.core import GitFlow
from gitflow.exceptions import NoSuchBranchError, AlreadyInitialized
from gitflow.bin import (main as Main,
                         VersionCommand, StatusCommand, InitCommand,
                         FeatureCommand, ReleaseCommand, HotfixCommand,
                         SupportCommand
                         )

from gitflow.branches import BranchManager
from tests.helpers import (copy_from_fixture, remote_clone_from_fixture,
                           all_commits, sandboxed)
from tests.helpers.factory import create_sandbox, create_git_repo



def capture_stdout(func):
    @wraps(func)
    def capture(*args, **kwargs):
        held, sys.stdout = sys.stdout, StringIO()
        try:
            return func(*args, **kwargs)
        finally:
            sys.stdout = held

    return capture

def runGitFlow(*argv):
    _argv, sys.argv = sys.argv, ['git-flow'] + list(argv)
    try:
        gitflow.bin.main()
    finally:
        sys.argv = _argv
    

class TestVersionCommand(TestCase):

    @capture_stdout
    def test_version(self):
        runGitFlow('version')
        stdout = sys.stdout.getvalue()
        self.assertEqual(gitflow.__version__+'\n', stdout)


class TestStatusCommand(TestCase):

    @capture_stdout
    @copy_from_fixture('sample_repo')
    def test_version(self):
        runGitFlow('status')
        stdout = sys.stdout.getvalue()
        self.assertItemsEqual([
            '  devel: 2b34cd2',
            '  feat/even: e56be18',
            '* feat/recursion: 54d59c8',
            '  stable: 296586b',
            ], stdout.splitlines())


class TestInitCommand(TestCase):
    @sandboxed
    def test_init_defaults(self):
        runGitFlow('init', '--defaults')
        gitflow = GitFlow('.')
        gitflow.init()
        self.assertEquals('origin', gitflow.origin_name())
        self.assertEquals('master', gitflow.master_name())
        self.assertEquals('develop', gitflow.develop_name())
        self.assertEquals('feature/', gitflow.get_prefix('feature'))
        self.assertEquals('release/', gitflow.get_prefix('release'))
        self.assertEquals('hotfix/', gitflow.get_prefix('hotfix'))
        self.assertEquals('support/', gitflow.get_prefix('support'))
        self.assertEquals('', gitflow.get_prefix('versiontag'))

    @sandboxed
    def test_init_accepting_defaults(self):
        text = '\n'*8
        _stdin, sys.stdin = sys.stdin, StringIO(text)
        try:
            runGitFlow('init')
        finally:
            sys.stdin = _stdin
        gitflow = GitFlow('.')
        gitflow.init()
        self.assertEquals('origin', gitflow.origin_name())
        self.assertEquals('master', gitflow.master_name())
        self.assertEquals('develop', gitflow.develop_name())
        self.assertEquals('feature/', gitflow.get_prefix('feature'))
        self.assertEquals('release/', gitflow.get_prefix('release'))
        self.assertEquals('hotfix/', gitflow.get_prefix('hotfix'))
        self.assertEquals('support/', gitflow.get_prefix('support'))
        self.assertEquals('', gitflow.get_prefix('versiontag'))

    @sandboxed
    def test_init_custom(self):
        text = '\n'.join(['my-remote', 'stable', 'devel',
                          'feat/', 'rel/', 'hf/', 'sup/', 'ver'])
        _stdin, sys.stdin = sys.stdin, StringIO(text)
        try:
            runGitFlow('init')
        finally:
            sys.stdin = _stdin
        gitflow = GitFlow('.')
        gitflow.init()
        self.assertEquals('my-remote', gitflow.origin_name())
        self.assertEquals('stable', gitflow.master_name())
        self.assertEquals('devel', gitflow.develop_name())
        self.assertEquals('feat/', gitflow.get_prefix('feature'))
        self.assertEquals('rel/', gitflow.get_prefix('release'))
        self.assertEquals('hf/', gitflow.get_prefix('hotfix'))
        self.assertEquals('sup/', gitflow.get_prefix('support'))
        self.assertEquals('ver', gitflow.get_prefix('versiontag'))

    @sandboxed
    def test_init_custom_accepting_some_defaults(self):
        text = '\n'.join(['my-remote', '', 'devel',
                          'feat/', '', '', 'sup/', 'v'])
        _stdin, sys.stdin = sys.stdin, StringIO(text)
        try:
            runGitFlow('init')
        finally:
            sys.stdin = _stdin
        gitflow = GitFlow('.')
        gitflow.init()
        self.assertEquals('my-remote', gitflow.origin_name())
        self.assertEquals('master', gitflow.master_name())
        self.assertEquals('devel', gitflow.develop_name())
        self.assertEquals('feat/', gitflow.get_prefix('feature'))
        self.assertEquals('release/', gitflow.get_prefix('release'))
        self.assertEquals('hotfix/', gitflow.get_prefix('hotfix'))
        self.assertEquals('sup/', gitflow.get_prefix('support'))
        self.assertEquals('v', gitflow.get_prefix('versiontag'))


    @copy_from_fixture('custom_repo')
    def test_init_fails_if_already_initialized(self):
        self.assertRaises(AlreadyInitialized, runGitFlow, 'init')


    @copy_from_fixture('custom_repo')
    def test_init_force_defaults_succeeds_if_already_initialized(self):
        runGitFlow('init', '--defaults', '--force')
        gitflow = GitFlow('.')
        gitflow.init()
        # these are the values already defined in custom_repo
        self.assertEquals('origin', gitflow.origin_name())
        self.assertEquals('production', gitflow.master_name())
        self.assertEquals('master', gitflow.develop_name())
        self.assertEquals('f-', gitflow.get_prefix('feature'))
        self.assertEquals('rel-', gitflow.get_prefix('release'))
        self.assertEquals('hf-', gitflow.get_prefix('hotfix'))
        self.assertEquals('supp-', gitflow.get_prefix('support'))
        self.assertEquals('v', gitflow.get_prefix('versiontag'))

    @copy_from_fixture('custom_repo')
    def test_init_existing_repo_fails_on_non_existing_master_branch(self):
        text = '\n'.join(['', 'stable', '', '', '', '', '', ''])
        _stdin, sys.stdin = sys.stdin, StringIO(text)
        try:
            self.assertRaises(NoSuchBranchError, runGitFlow, 'init', '--force')
        finally:
            sys.stdin = _stdin

    @copy_from_fixture('custom_repo')
    def test_init_existing_repo_fails_on_non_existing_develop_branch(self):
        text = '\n'.join(['', '', 'workinprogress', '', '', '', '', ''])
        _stdin, sys.stdin = sys.stdin, StringIO(text)
        try:
            self.assertRaises(NoSuchBranchError, runGitFlow, 'init', '--force')
        finally:
            sys.stdin = _stdin

    @copy_from_fixture('custom_repo')
    def test_init_force_succeeds_if_already_initialized(self):
        # NB: switching master and develop 
        text = '\n'.join(['my-remote', 'master', 'production',
                          'feat/', 'rel/', 'hf/', 'sup/', 'ver'])
        _stdin, sys.stdin = sys.stdin, StringIO(text)
        try:
            runGitFlow('init', '--force')
        finally:
            sys.stdin = _stdin
        gitflow = GitFlow('.')
        gitflow.init()
        self.assertEquals('master', gitflow.master_name())
        self.assertEquals('production', gitflow.develop_name())

    @sandboxed
    def test_init_fails_if_develop_name_equals_master_name(self):
        text = '\n'.join(['', 'mainbranch', 'mainbranch'])
        _stdin, sys.stdin = sys.stdin, StringIO(text)
        try:
            self.assertRaisesRegexp(SystemExit, ".*branches should differ.*",
                                    runGitFlow, 'init')
        finally:
            sys.stdin = _stdin

    # These tests need a repo with only branches `foo` and `bar`
    # or other names not selected for defaults
    # :todo: give no master branch name (or white-spaces)
    # :todo: give no develop branch name (or white-spaces)
