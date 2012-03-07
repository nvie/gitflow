#
# This file is part of `gitflow`.
# Copyright (c) 2010-2011 Vincent Driessen
# Copyright (c) 2012 Hartmut Goebel
# Distributed under a BSD-like license. For full terms see the file LICENSE.txt
#

import sys
import re
from functools import wraps
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from unittest2 import TestCase

import gitflow
from gitflow.core import GitFlow, Repo
from gitflow.exceptions import (NoSuchBranchError, NoSuchRemoteError,
                                AlreadyInitialized, NotInitialized,
                                BaseNotOnBranch)
from gitflow.bin import (main as Main,
                         VersionCommand, StatusCommand, InitCommand,
                         FeatureCommand, ReleaseCommand, HotfixCommand,
                         SupportCommand
                         )

from gitflow.branches import BranchManager
from tests.helpers import (copy_from_fixture, remote_clone_from_fixture,
                           all_commits, sandboxed, fake_commit)
from tests.helpers.factory import create_sandbox, create_git_repo

__copyright__ = "2010-2011 Vincent Driessen; 2012 Hartmut Goebel"
__license__ = "BSD"

def runGitFlow(*argv, **kwargs):
    capture = kwargs.get('capture', False)
    _argv, sys.argv = sys.argv, ['git-flow'] + list(argv)
    _stdout = sys.stdout
    try:
        if not capture:
            gitflow.bin.main()
        else:
            sys.stdout = StringIO()
            gitflow.bin.main()
            return sys.stdout.getvalue()
    finally:
        sys.stdout = _stdout
        sys.argv = _argv


class TestCase(TestCase):
    def assertArgparseError(self, expected_regexp, func, *args, **kwargs):
        _stderr, sys.stderr = sys.stderr, StringIO()
        try:
            self.assertRaises(SystemExit, func, *args, **kwargs)
            msg = sys.stderr.getvalue()
            expected_regexp = re.compile(expected_regexp)
            if not expected_regexp.search(str(msg)):
                raise self.failureException('"%s" does not match "%s"' %
                         (expected_regexp.pattern, msg))
        finally:
            sys.stderr = _stderr

class TestVersionCommand(TestCase):

    def test_version(self):
        stdout = runGitFlow('version', capture=1)
        self.assertEqual(gitflow.__version__+'\n', stdout)


class TestStatusCommand(TestCase):

    @copy_from_fixture('sample_repo')
    def test_version(self):
        stdout = runGitFlow('status', capture=1)
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
        gitflow = GitFlow('.').init()
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
        gitflow = GitFlow('.').init()
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
        gitflow = GitFlow('.').init()
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
        gitflow = GitFlow('.').init()
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
        gitflow = GitFlow('.').init()
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
        gitflow = GitFlow('.').init()
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


    @remote_clone_from_fixture('sample_repo')
    def test_subcommands_requiring_initialized_repo(self):
        def assertSystemExit(*args):
            self.assertRaisesRegexp(
                SystemExit, 'repo has not yet been initialized for git-flow',
                runGitFlow, 'feature', *args)
        def assertNotInitialized(*args):
            self.assertRaises(NotInitialized,
                runGitFlow, 'feature', *args)
        assertNotInitialized('start', 'xxx')
        assertNotInitialized('finish', 'recursion')
        assertNotInitialized('publish', 'recursion')
        assertNotInitialized('track', 'recursion')
        assertNotInitialized('diff', 'recursion')
        assertNotInitialized('rebase', 'recursion')
        assertNotInitialized('pull', 'even')


class TestFeature(TestCase):

    @copy_from_fixture('sample_repo')
    def test_feature_list(self):
        stdout = runGitFlow('feature', 'list', capture=1)
        expected = [
          '  even',
          '* recursion'
          ]
        self.assertEqual(stdout.splitlines(), expected)

    @copy_from_fixture('sample_repo')
    def test_feature_list_verbose(self):
        stdout = runGitFlow('feature', 'list', '--verbose', capture=1)
        expected = [
          '  even      (based on latest devel)',
          '* recursion (based on latest devel)'
          ]
        self.assertEqual(stdout.splitlines(), expected)

    @copy_from_fixture('sample_repo')
    def test_feature_list_verbose_rebased(self):
        self.repo.refs['devel'].checkout()
        fake_commit(self.repo, 'A commit on devel')
        stdout = runGitFlow('feature', 'list', '--verbose', capture=1)
        expected = [
          '  even      (may be rebased)',
          '  recursion (may be rebased)'
          ]
        self.assertEqual(stdout.splitlines(), expected)

    @sandboxed
    def test_feature_list_verbose_no_commits(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        repo.create_head('feature/wow', 'HEAD')
        stdout = runGitFlow('feature', 'list', '--verbose', capture=1)
        expected = [
          '  wow (no commits yet)'
          ]
        self.assertEqual(stdout.splitlines(), expected)

    @copy_from_fixture('sample_repo')
    def test_feature_list_verbose_ff(self):
        self.repo.create_head('devel', 'feat/recursion', force=1)
        self.repo.refs['devel'].checkout()
        fake_commit(self.repo, 'A commit on devel')
        stdout = runGitFlow('feature', 'list', '--verbose', capture=1)
        expected = [
          '  even      (may be rebased)',
          '  recursion (is behind devel, may ff)'
          ]
        self.assertEqual(stdout.splitlines(), expected)

    #--- feature start ---

    @copy_from_fixture('sample_repo')
    def test_feature_start(self):
        runGitFlow('feature', 'start', 'wow-feature')
        self.assertIn('feat/wow-feature', Repo().branches)

    @copy_from_fixture('sample_repo')
    def test_feature_start_alt_base(self):
        runGitFlow('feature', 'start', 'wow-feature', 'devel')
        self.assertIn('feat/wow-feature', Repo().branches)

    ## feature branch is not required to start at `develop`, rethink this
    ## @copy_from_fixture('sample_repo')
    ## def test_feature_start_wrong_alt_base_raises_error(self):
    ##     self.repo.refs['stable'].checkout()
    ##     fake_commit(self.repo, 'A fake commit on stable')
    ##     self.assertRaises(BaseNotOnBranch,
    ##                       runGitFlow, 'feature', 'start', 'wow', 'stable')

    @copy_from_fixture('sample_repo')
    def test_feature_start_empty_name(self):
        self.assertArgparseError('must not by empty',
                                 runGitFlow, 'feature', 'start', '')
        self.assertArgparseError('must not by empty',
                                 runGitFlow, 'feature', 'start', '', 'devel')

    @copy_from_fixture('sample_repo')
    def test_feature_start_no_name(self):
        self.assertArgparseError('too few arguments',
                                 runGitFlow, 'feature', 'start')

    #--- feature finish ---

    @remote_clone_from_fixture('sample_repo')
    def test_feature_finish(self):
        GitFlow('.').init()
        runGitFlow('feature', 'finish', 'recursion')
        self.assertNotIn('feat/recursion', Repo().branches)

    @copy_from_fixture('sample_repo')
    def test_feature_finish_current(self):
        GitFlow('.').init()
        runGitFlow('feature', 'finish')
        self.assertNotIn('feat/recursion', Repo().branches)

    @copy_from_fixture('sample_repo')
    def test_feature_finish_empty_prefix(self):
        GitFlow('.').init()
        runGitFlow('feature', 'checkout', 'even')
        runGitFlow('feature', 'finish', '')
        self.assertNotIn('feat/even', Repo().branches)

    @copy_from_fixture('sample_repo')
    def test_feature_finish_prefix(self):
        GitFlow('.').init()
        runGitFlow('feature', 'finish', 'e')
        self.assertNotIn('feat/even', Repo().branches)

    @copy_from_fixture('sample_repo')
    def test_feature_finish_rebase(self):
        gitflow = GitFlow('.').init()
        gitflow.develop().checkout()
        fake_commit(gitflow.repo, 'A commit on devel')
        runGitFlow('feature', 'finish', 'even', '--rebase')
        self.assertNotIn('feat/even', Repo().branches)
        self.assertEqual(gitflow.develop().commit.message,
                         'Finished feature even.\n')
        # :todo: think about some other test to see if it really worked

    #:todo: test-cases for `feature finish --rebase` w/ conflict

    @copy_from_fixture('sample_repo')
    def test_feature_finish_keep(self):
        GitFlow('.').init()
        runGitFlow('feature', 'finish', 'even', '--keep')
        self.assertIn('feat/even', Repo().branches)

    #:todo: test-cases for `feature finish --fetch`
    #:todo: test-cases for `feature finish --force-delete`

    #--- feature publish ---

    @remote_clone_from_fixture('sample_repo')
    def test_feature_publish(self):
        GitFlow('.').init()
        runGitFlow('feature', 'start', 'wow')
        runGitFlow('feature', 'publish', 'wow')
        self.assertIn('feat/wow', Repo().remotes['my-remote'].refs)

    @remote_clone_from_fixture('sample_repo')
    def test_feature_publish_current(self):
        GitFlow('.').init()
        runGitFlow('feature', 'start', 'wow')
        runGitFlow('feature', 'publish')
        self.assertIn('feat/wow', Repo().remotes['my-remote'].refs)

    @remote_clone_from_fixture('sample_repo')
    def test_feature_publish_empty_prefix(self):
        GitFlow('.').init()
        runGitFlow('feature', 'start', 'wow')
        runGitFlow('feature', 'publish', '')
        self.assertIn('feat/wow', Repo().remotes['my-remote'].refs)

    @remote_clone_from_fixture('sample_repo')
    def test_feature_publish_prefix(self):
        GitFlow('.').init()
        runGitFlow('feature', 'start', 'wow')
        runGitFlow('feature', 'publish', 'w')
        self.assertIn('feat/wow', Repo().remotes['my-remote'].refs)

    #--- feature track ---

    @remote_clone_from_fixture('sample_repo')
    def test_feature_track(self):
        GitFlow('.').init()
        runGitFlow('feature', 'track', 'even')

    @remote_clone_from_fixture('sample_repo')
    def test_feature_track_name_is_required(self):
        GitFlow('.').init()
        self.assertArgparseError('too few arguments',
                                 runGitFlow, 'feature', 'track')
        self.assertArgparseError('must not by empty',
                                 runGitFlow, 'feature', 'track', '')

    #--- feature diff ---

    @copy_from_fixture('sample_repo')
    def test_feature_diff(self):
        runGitFlow('feature', 'diff', 'recursion')

    @copy_from_fixture('sample_repo')
    def test_feature_diff_current(self):
        runGitFlow('feature', 'diff')

    @copy_from_fixture('sample_repo')
    def test_feature_diff_empty_prefix(self):
        runGitFlow('feature', 'diff', '')

    @copy_from_fixture('sample_repo')
    def test_feature_diff_prefix(self):
        runGitFlow('feature', 'diff', 'rec')

    #--- feature rebase ---

    @copy_from_fixture('sample_repo')
    def test_feature_rebase(self):
        runGitFlow('feature', 'rebase', 'recursion')

    @copy_from_fixture('sample_repo')
    def test_feature_rebase_current(self):
        runGitFlow('feature', 'rebase')

    @copy_from_fixture('sample_repo')
    def test_feature_rebase_empty_prefix(self):
        runGitFlow('feature', 'rebase', '')

    @copy_from_fixture('sample_repo')
    def test_feature_rebase_prefix(self):
        runGitFlow('feature', 'rebase', 'rec')

    #--- feature  checkout ---

    @copy_from_fixture('sample_repo')
    def test_feature_checkout(self):
        runGitFlow('feature', 'checkout', 'even')

    @copy_from_fixture('sample_repo')
    def test_feature_checkout_current(self):
        self.assertArgparseError('too few arguments',
                                 runGitFlow, 'feature', 'checkout')

    @copy_from_fixture('sample_repo')
    def test_feature_checkout_empty_prefix(self):
        self.assertArgparseError('must not by empty',
                                 runGitFlow, 'feature', 'checkout', '')

    @copy_from_fixture('sample_repo')
    def test_feature_checkout_prefix(self):
        runGitFlow('feature', 'checkout', 'rec')

    #--- feature pull ---

    @remote_clone_from_fixture('sample_repo')
    def test_feature_pull(self):
        GitFlow('.').init()
        runGitFlow('feature', 'pull', 'my-remote', 'even')

    @remote_clone_from_fixture('sample_repo')
    def test_feature_pull_empty_remote_raises_error(self):
        GitFlow('.').init()
        self.assertArgparseError('must not by empty',
                                 runGitFlow, 'feature', 'pull', '', 'even')

    @remote_clone_from_fixture('sample_repo')
    def test_feature_pull_nonexisting_remote_raises_error(self):
        GitFlow('.').init()
        self.assertRaises(NoSuchRemoteError,
                          runGitFlow, 'feature', 'pull', 'some-remote', 'even')

    @remote_clone_from_fixture('sample_repo')
    def test_feature_pull_name_is_required(self):
        GitFlow('.').init()
        self.assertRaises(NoSuchBranchError, runGitFlow, 'feature', 'pull', 'my-remote')
        self.assertRaises(NoSuchBranchError, runGitFlow, 'feature', 'pull', 'my-remote', '')


class TestRelease(TestCase):

    @copy_from_fixture('release')
    def test_release_list(self):
        stdout = runGitFlow('release', 'list', capture=1)
        expected = [
          '  1.0'
          ]
        self.assertEqual(stdout.splitlines(), expected)

    @copy_from_fixture('release')
    def test_release_list_verbose(self):
        stdout = runGitFlow('release', 'list', '--verbose', capture=1)
        expected = [
          '  1.0 (based on latest devel)'
          ]
        self.assertEqual(stdout.splitlines(), expected)


    #--- release start ---

    @copy_from_fixture('sample_repo')
    def test_release_start(self):
        runGitFlow('release', 'start', '1.1')
        self.assertIn('rel/1.1', Repo().branches)

    @copy_from_fixture('sample_repo')
    def test_release_start_alt_base(self):
        runGitFlow('release', 'start', '1.1', 'devel')
        self.assertIn('rel/1.1', Repo().branches)

    @copy_from_fixture('sample_repo')
    def test_release_start_wrong_alt_base_raises_error(self):
        self.repo.refs['stable'].checkout()
        fake_commit(self.repo, 'A fake commit on stable')
        self.assertRaises(BaseNotOnBranch,
                          runGitFlow, 'release', 'start', 'wow', 'stable')

    @copy_from_fixture('release')
    def test_release_start_empty_name(self):
        self.assertArgparseError('must not by empty',
                                 runGitFlow, 'release', 'start', '')

    @copy_from_fixture('release')
    def test_release_start_no_name(self):
        self.assertArgparseError('too few arguments',
                                 runGitFlow, 'release', 'start')

    #--- release finish ---

    @copy_from_fixture('release')
    def test_release_finish(self):
        gitflow = GitFlow('.').init()
        gitflow.checkout('release', '1.0')
        runGitFlow('release', 'finish', '1.0')
        self.assertNotIn('rel/1.0', Repo().branches)

    @copy_from_fixture('release')
    def test_release_finish_current(self):
        gitflow = GitFlow('.').init()
        gitflow.checkout('release', '1.0')
        runGitFlow('release', 'finish')
        self.assertNotIn('rel/1.0', Repo().branches)

    @copy_from_fixture('release')
    def test_release_finish_empty_prefix(self):
        gitflow = GitFlow('.').init()
        gitflow.checkout('release', '1.0')
        runGitFlow('release', 'finish', '')
        self.assertNotIn('rel/1.0', Repo().branches)

    @copy_from_fixture('release')
    def test_release_finish_prefix(self):
        gitflow = GitFlow('.').init()
        gitflow.checkout('release', '1.0')
        # release finish requires a name, not a prefix
        self.assertRaises(NoSuchBranchError,
                          runGitFlow, 'release', 'finish', '1')

    #:todo: test-cases for `release finish --rebase`
    #:todo: test-cases for `release finish --fetch`
    #:todo: test-cases for `release finish --keep`
    #:todo: test-cases for `release finish --force-delete`

    #--- release publish ---

    @remote_clone_from_fixture('sample_repo')
    def test_release_publish(self):
        GitFlow('.').init()
        runGitFlow('release', 'start', '1.1')
        runGitFlow('release', 'publish', '1.1')
        self.assertIn('rel/1.1', Repo().remotes['my-remote'].refs)

    @remote_clone_from_fixture('sample_repo')
    def test_release_publish_current(self):
        GitFlow('.').init()
        runGitFlow('release', 'start', '1.1')
        runGitFlow('release', 'publish')
        self.assertIn('rel/1.1', Repo().remotes['my-remote'].refs)

    @remote_clone_from_fixture('sample_repo')
    def test_release_publish_empty_prefix(self):
        GitFlow('.').init()
        runGitFlow('release', 'start', '1.1')
        runGitFlow('release', 'publish', '')
        self.assertIn('rel/1.1', Repo().remotes['my-remote'].refs)

    @remote_clone_from_fixture('sample_repo')
    def test_release_publish_prefix(self):
        GitFlow('.').init()
        runGitFlow('release', 'start', '1.1')
        self.assertRaises(NoSuchBranchError,
                          runGitFlow, 'release', 'publish', '1')

    #--- release track ---

    @remote_clone_from_fixture('release')
    def test_release_track(self):
        GitFlow('.').init()
        runGitFlow('release', 'track', '1.0')

    @remote_clone_from_fixture('sample_repo')
    def test_release_track_name_is_required(self):
        GitFlow('.').init()
        self.assertArgparseError('too few arguments',
                                 runGitFlow, 'release', 'track')
        self.assertArgparseError('must not by empty',
                                 runGitFlow, 'release', 'track', '')

    #--- unsupported `release` subcommands ---

    def test_release_diff_is_no_valid_subcommand(self):
        self.assertArgparseError("invalid choice: 'diff'",
                                 runGitFlow, 'release', 'diff')

    def test_release_rebase_is_no_valid_subcommand(self):
        self.assertArgparseError("invalid choice: 'rebase'",
                                 runGitFlow, 'release', 'rebase')

    def test_release_checkout_is_no_valid_subcommand(self):
        self.assertArgparseError("invalid choice: 'checkout'",
                                 runGitFlow, 'release', 'checkout')

    def test_release_pull_is_no_valid_subcommand(self):
        self.assertArgparseError("invalid choice: 'pull'",
                                 runGitFlow, 'release', 'pull')


class TestHotfix(TestCase):

    @copy_from_fixture('sample_repo')
    def test_hotfix_list(self):
        self.repo.create_head('hf/2.3', 'HEAD')
        stdout = runGitFlow('hotfix', 'list', capture=1)
        expected = [
          '  2.3'
          ]
        self.assertEqual(stdout.splitlines(), expected)

    @copy_from_fixture('sample_repo')
    def test_hotfix_list_verbose(self):
        self.repo.create_head('hf/2.3', 'HEAD')
        stdout = runGitFlow('hotfix', 'list', '--verbose', capture=1)
        expected = [
          '  2.3 (based on latest stable)'
          ]
        self.assertEqual(stdout.splitlines(), expected)

    @copy_from_fixture('release')
    def test_hotfix_list_verbose_tagged(self):
        runGitFlow('release', 'finish', '1.0')
        runGitFlow('hotfix', 'start', '1.0.1')
        fake_commit(self.repo, 'Hotfix commit.')
        stdout = runGitFlow('hotfix', 'list', '--verbose', capture=1)
        expected = [
          '* 1.0.1 (based on v1.0)'
          ]
        self.assertEqual(stdout.splitlines(), expected)

    #--- hotfix start ---

    @copy_from_fixture('sample_repo')
    def test_hotfix_start(self):
        runGitFlow('hotfix', 'start', 'wow-hotfix')
        self.assertIn('hf/wow-hotfix', Repo().branches)

    @copy_from_fixture('sample_repo')
    def test_hotfix_start_alt_base(self):
        runGitFlow('hotfix', 'start', 'wow-hotfix', 'stable')
        self.assertIn('hf/wow-hotfix', Repo().branches)

    @copy_from_fixture('sample_repo')
    def test_hotfix_start_wrong_alt_base_raises_error(self):
        self.assertRaises(BaseNotOnBranch,
                          runGitFlow, 'hotfix', 'start', 'wow-feature', 'devel')

    @copy_from_fixture('sample_repo')
    def test_hotfix_start_empty_name(self):
        self.assertArgparseError('must not by empty',
                                 runGitFlow, 'hotfix', 'start', '')

    @copy_from_fixture('sample_repo')
    def test_hotfix_start_no_name(self):
        self.assertArgparseError('too few arguments',
                                 runGitFlow, 'hotfix', 'start')

    #--- hotfix finish ---

    @remote_clone_from_fixture('sample_repo')
    def test_hotfix_finish(self):
        GitFlow('.').init()
        runGitFlow('hotfix', 'start', 'fast')
        self.assertIn('hf/fast', Repo().branches)
        runGitFlow('hotfix', 'finish', 'fast')
        self.assertNotIn('hf/fast', Repo().branches)

    @copy_from_fixture('sample_repo')
    def test_hotfix_finish_current(self):
        GitFlow('.').init()
        runGitFlow('hotfix', 'start', 'fast')
        runGitFlow('hotfix', 'finish')
        self.assertNotIn('hf/fast', Repo().branches)

    @copy_from_fixture('sample_repo')
    def test_hotfix_finish_empty_prefix(self):
        GitFlow('.').init()
        runGitFlow('hotfix', 'start', 'fast')
        runGitFlow('hotfix', 'finish', '')
        self.assertNotIn('hf/fast', Repo().branches)

    @copy_from_fixture('sample_repo')
    def test_hotfix_finish_prefix(self):
        GitFlow('.').init()
        runGitFlow('hotfix', 'start', 'fast')
        self.assertRaises(NoSuchBranchError,
                          runGitFlow, 'hotfix', 'finish', 'f')

    #:todo: test-cases for `hotfix finish --rebase`
    #:todo: test-cases for `hotfix finish --fetch`
    #:todo: test-cases for `hotfix finish --keep`
    #:todo: test-cases for `hotfix finish --force-delete`

    #--- hotfix publish ---

    @remote_clone_from_fixture('sample_repo')
    def test_hotfix_publish(self):
        GitFlow('.').init()
        runGitFlow('hotfix', 'start', 'wow')
        runGitFlow('hotfix', 'publish', 'wow')
        self.assertIn('hf/wow', Repo().remotes['my-remote'].refs)

    @remote_clone_from_fixture('sample_repo')
    def test_hotfix_publish_current(self):
        GitFlow('.').init()
        runGitFlow('hotfix', 'start', 'wow')
        runGitFlow('hotfix', 'publish')
        self.assertIn('hf/wow', Repo().remotes['my-remote'].refs)

    @remote_clone_from_fixture('sample_repo')
    def test_hotfix_publish_empty_prefix(self):
        GitFlow('.').init()
        runGitFlow('hotfix', 'start', 'wow')
        runGitFlow('hotfix', 'publish', '')
        self.assertIn('hf/wow', Repo().remotes['my-remote'].refs)

    @remote_clone_from_fixture('sample_repo')
    def test_hotfix_publish_prefix(self):
        GitFlow('.').init()
        runGitFlow('hotfix', 'start', 'wow')
        self.assertRaises(NoSuchBranchError,
                          runGitFlow, 'hotfix', 'publish', 'w')

    #--- unsupported `hotfix` subcommands ---

    def test_hotfix_track_is_no_valid_subcommand(self):
        self.assertArgparseError("invalid choice: 'track'",
                                 runGitFlow, 'hotfix', 'track')

    def test_hotfix_diff_is_no_valid_subcommand(self):
        self.assertArgparseError("invalid choice: 'diff'",
                                 runGitFlow, 'hotfix', 'diff')

    def test_hotfix_rebase_is_no_valid_subcommand(self):
        self.assertArgparseError("invalid choice: 'rebase'",
                                 runGitFlow, 'hotfix', 'rebase')

    def test_hotfix_checkout_is_no_valid_subcommand(self):
        self.assertArgparseError("invalid choice: 'checkout'",
                                 runGitFlow, 'hotfix', 'checkout')

    def test_hotfix_pull_is_no_valid_subcommand(self):
        self.assertArgparseError("invalid choice: 'pull'",
                                 runGitFlow, 'hotfix', 'pull')

class TestSupport(TestCase):

    @copy_from_fixture('sample_repo')
    def test_support_list(self):
        self.repo.create_head('supp/1.0-22', 'HEAD')
        stdout = runGitFlow('support', 'list', capture=1)
        expected = [
          '  1.0-22'
          ]
        self.assertEqual(stdout.splitlines(), expected)

    @copy_from_fixture('sample_repo')
    def test_support_list_verbose(self):
        self.repo.create_head('supp/1.0-22', 'HEAD')
        stdout = runGitFlow('support', 'list', '--verbose', capture=1)
        expected = [
          '  1.0-22 (based on latest stable)'
          ]
        self.assertEqual(stdout.splitlines(), expected)

    @copy_from_fixture('release')
    def test_support_list_verbose_tagged(self):
        runGitFlow('release', 'finish', '1.0')
        runGitFlow('support', 'start', '1.0-22')
        fake_commit(self.repo, 'Support commit.')
        stdout = runGitFlow('support', 'list', '--verbose', capture=1)
        expected = [
          '* 1.0-22 (based on v1.0)'
          ]
        self.assertEqual(stdout.splitlines(), expected)

    #--- support start ---

    @copy_from_fixture('sample_repo')
    def test_support_start(self):
        runGitFlow('support', 'start', 'wow-support')
        self.assertIn('supp/wow-support', Repo().branches)

    @copy_from_fixture('sample_repo')
    def test_support_start_alt_base(self):
        runGitFlow('support', 'start', 'wow-support', 'stable')
        self.assertIn('supp/wow-support', Repo().branches)

    @copy_from_fixture('sample_repo')
    def test_support_start_wrong_alt_base_raises_error(self):
        self.assertRaises(BaseNotOnBranch,
                          runGitFlow, 'support', 'start', 'wow-support', 'devel')

    @copy_from_fixture('sample_repo')
    def test_support_start_empty_name(self):
        self.assertArgparseError('must not by empty',
                                 runGitFlow, 'support', 'start', '')

    @copy_from_fixture('sample_repo')
    def test_support_start_no_name(self):
        self.assertArgparseError('too few arguments',
                                 runGitFlow, 'support', 'start')


    #--- unsupported `support` subcommands ---

    def test_support_publish_is_no_valid_subcommand(self):
        self.assertArgparseError("invalid choice: 'finish'",
                                 runGitFlow, 'support', 'finish')

    def test_support_track_is_no_valid_subcommand(self):
        self.assertArgparseError("invalid choice: 'track'",
                                 runGitFlow, 'support', 'track')

    def test_support_diff_is_no_valid_subcommand(self):
        self.assertArgparseError("invalid choice: 'diff'",
                                 runGitFlow, 'support', 'diff')

    def test_support_rebase_is_no_valid_subcommand(self):
        self.assertArgparseError("invalid choice: 'rebase'",
                                 runGitFlow, 'support', 'rebase')

    def test_support_checkout_is_no_valid_subcommand(self):
        self.assertArgparseError("invalid choice: 'checkout'",
                                 runGitFlow, 'support', 'checkout')

    def test_support_pull_is_no_valid_subcommand(self):
        self.assertArgparseError("invalid choice: 'pull'",
                                 runGitFlow, 'support', 'pull')
