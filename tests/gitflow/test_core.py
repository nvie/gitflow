#
# This file is part of `gitflow`.
# Copyright (c) 2010-2011 Vincent Driessen
# Copyright (c) 2012 Hartmut Goebel
# Distributed under a BSD-like license. For full terms see the file LICENSE.txt
#

from unittest2 import TestCase
import os
import sys
try:
    import cStringIO as StringIO
except:
    import StringIO
from ConfigParser import NoOptionError, NoSectionError

from git import GitCommandError

from gitflow.core import GitFlow
from gitflow.branches import BranchManager
from gitflow.exceptions import (BranchExistsError, NotInitialized,
                                NoSuchBranchError, NoSuchRemoteError,
                                MergeConflict, BadObjectError)
from tests.helpers import (copy_from_fixture, remote_clone_from_fixture,
                           fake_commit, all_commits, set_gnupg_home)
from tests.helpers.factory import create_sandbox, create_git_repo

__copyright__ = "2010-2011 Vincent Driessen; 2012 Hartmut Goebel"
__license__ = "BSD"

class TestGitFlowBasics(TestCase):

    # Configuration
    @copy_from_fixture('custom_repo')
    def test_config_reader(self):
        gitflow = GitFlow(self.repo).init()
        self.assertRaises(ValueError, gitflow.get,
                'invalid_setting_since_this_has_no_dot')
        self.assertRaises(NoSectionError, gitflow.get,
                'nonexisting.nonexisting')
        self.assertRaises(NoSectionError, gitflow.get,
                'section.subsection.propname')
        self.assertRaises(NoOptionError, gitflow.get, 'foo.nonexisting')
        self.assertEquals('qux', gitflow.get('foo.bar'))

    @copy_from_fixture('custom_repo')
    def test_custom_branchnames(self):
        gitflow = GitFlow(self.repo).init()
        self.assertEquals('production', gitflow.master_name())
        self.assertEquals('master', gitflow.develop_name())
        self.assertEquals('origin', gitflow.origin_name())
        self.assertEquals('f-', gitflow.get_prefix('feature'))
        self.assertEquals('rel-', gitflow.get_prefix('release'))
        self.assertEquals('hf-', gitflow.get_prefix('hotfix'))
        self.assertEquals('supp-', gitflow.get_prefix('support'))
        self.assertEquals('v', gitflow.get_prefix('versiontag'))


    # Initialization
    def test_branch_names_fails_in_new_sandbox(self):
        sandbox = create_sandbox(self)
        gitflow = GitFlow(sandbox)
        self.assertRaises(NotInitialized, gitflow.branch_names)

    def test_empty_repo_has_no_branches(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        self.assertItemsEqual([], gitflow.branch_names())

    @copy_from_fixture('custom_repo')
    def test_custom_repo_has_branches(self):
        gitflow = GitFlow(self.repo).init()
        self.assertItemsEqual(['master', 'production'],
                gitflow.branch_names())

    @copy_from_fixture('custom_repo')
    def test_custom_repo_init_keeps_active_branch_if_develop_already_existed(self):
        active_branch = self.repo.active_branch
        gitflow = GitFlow(self.repo).init()
        self.assertNotEqual(gitflow.repo.active_branch.name, active_branch)

    def test_origin_without_remote_raises_error(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        self.assertRaises(NoSuchRemoteError, gitflow.origin)

    # Sanity checking
    def test_new_repo_is_not_dirty(self):
        sandbox = create_sandbox(self)
        gitflow = GitFlow(sandbox).init()
        self.assertFalse(gitflow.is_dirty())

    @copy_from_fixture('dirty_sample_repo')
    def test_existing_repo_is_not_dirty(self):
        gitflow = GitFlow(self.repo)
        self.assertTrue(gitflow.is_dirty())

    def test_new_repo_has_no_staged_commits(self):
        sandbox = create_sandbox(self)
        gitflow = GitFlow(sandbox).init()
        self.assertFalse(gitflow.has_staged_commits())

    @copy_from_fixture('dirty_sample_repo')
    def test_existing_repo_has_staged_commits(self):
        gitflow = GitFlow(self.repo)
        self.assertTrue(gitflow.has_staged_commits())

    def test_gitflow_cannot_get_status_on_empty_sandbox(self):
        sandbox = create_sandbox(self)
        gitflow = GitFlow(sandbox)
        self.assertRaises(NotInitialized, gitflow.status)

    def test_gitflow_status_on_fresh_repo(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        self.assertEquals([], gitflow.status())

    @copy_from_fixture('sample_repo')
    def test_gitflow_status_on_sample_repo(self):
        gitflow = GitFlow(self.repo)
        self.assertItemsEqual([
                ('stable', '296586bb164c946cad10d37e82570f60e6348df9', False),
                ('devel', '2b34cd2e1617e5f0d4e077c6ec092b9f50ed49a3', False),
                ('feat/recursion', '54d59c872469c7bf34d540d2fb3128a97502b73f', True),
                ('feat/even', 'e56be18dada9e81ca7969760ddea357b0c4c9412', False),
            ], gitflow.status())


    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_status_on_cloned_sample_repo(self):
        gitflow = GitFlow(self.repo)
        # NB: only the active branch is created locally when cloning
        self.assertEqual(self.remote.active_branch.name, 'feat/recursion')
        self.assertItemsEqual([
                ('feat/recursion', '54d59c872469c7bf34d540d2fb3128a97502b73f', True),
            ], gitflow.status())

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_status_on_remote_sample_repo(self):
        gitflow = GitFlow(self.remote)
        self.assertItemsEqual([
                ('stable', '296586bb164c946cad10d37e82570f60e6348df9', False),
                ('devel', '2b34cd2e1617e5f0d4e077c6ec092b9f50ed49a3', False),
                ('feat/recursion', '54d59c872469c7bf34d540d2fb3128a97502b73f', True),
                ('feat/even', 'e56be18dada9e81ca7969760ddea357b0c4c9412', False),
            ], gitflow.status())


    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_cloned_sample_repo_is_not_remote(self):
        self.assertNotEqual(self.remote.git_dir, self.repo.git_dir)

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_cloned_sample_repo_equals_remote(self):
        # only the active branch (feat/recursion) is cloned which
        # includes devel and stable
        heads_to_check = [h.name for h in self.remote.heads]
        heads_to_check.remove('feat/even')
        self.assertIn('devel', heads_to_check)
        self.assertIn('stable', heads_to_check)
        all_remote_commits = all_commits(self.remote, heads_to_check)
        all_cloned_commits = all_commits(self.repo)
        self.assertEqual(all_remote_commits, all_cloned_commits)

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_cloned_sample_repo_remote_name(self):
        self.assertEqual(len(list(self.repo.remotes)), 1)
        self.assertEqual(self.repo.remotes[0].name, 'my-remote')

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_required_remote_returns_remote(self):
        gitflow = GitFlow(self.repo).init()
        remote = gitflow.require_remote('my-remote')
        self.assertEqual(self.repo.remotes['my-remote'], remote)

    def test_gitflow_required_remote_raises_error_on_nonexisting_remote(self):
        sandbox = create_sandbox(self)
        gitflow = GitFlow(sandbox).init()
        self.assertRaises(NoSuchRemoteError,
                          gitflow.require_remote, 'some-remote')

class TestGitFlowInit(TestCase):
    # git flow init

    def test_gitflow_init_inits_underlying_git_repo(self):
        sandbox = create_sandbox(self)
        gitflow = GitFlow(sandbox)
        dot_git_dir = os.path.join(sandbox, '.git')
        self.assertFalse(os.path.exists(dot_git_dir))
        gitflow.init()
        self.assertTrue(os.path.exists(dot_git_dir))
        self.assertTrue(gitflow.is_initialized())

    def test_gitflow_init_marks_initialized(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        self.assertFalse(gitflow.is_initialized())
        gitflow.init()
        self.assertTrue(gitflow.is_initialized())

    def test_gitflow_throws_errors_before_init(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        self.assertRaises(NotInitialized, gitflow.master_name)
        self.assertRaises(NotInitialized, gitflow.develop_name)
        self.assertRaises(NotInitialized, gitflow.get_prefix, 'feature')

    def test_gitflow_init_initializes_default_config(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        self.assertEquals('master', gitflow.master_name())
        self.assertEquals('develop', gitflow.develop_name())
        self.assertEquals('origin', gitflow.origin_name())
        self.assertEquals('feature/', gitflow.get_prefix('feature'))
        self.assertEquals('hotfix/', gitflow.get_prefix('hotfix'))
        self.assertEquals('release/', gitflow.get_prefix('release'))
        self.assertEquals('support/', gitflow.get_prefix('support'))
        self.assertEquals('', gitflow.get_prefix('versiontag'))

    def test_gitflow_init_with_alternative_config(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        prefixes = dict(feature='f-',
                        hotfix='hf-',
                        release='rel-',
                        support='supp-',
                        versiontag='ver')
        names = dict(origin='somewhereelse')
        gitflow.init(master='foo', develop='bar', prefixes=prefixes, names=names)
        self.assertEquals('foo', gitflow.master_name())
        self.assertEquals('bar', gitflow.develop_name())
        self.assertEquals('somewhereelse', gitflow.origin_name())
        self.assertEquals('f-', gitflow.get_prefix('feature'))
        self.assertEquals('rel-', gitflow.get_prefix('release'))
        self.assertEquals('hf-', gitflow.get_prefix('hotfix'))
        self.assertEquals('supp-', gitflow.get_prefix('support'))
        self.assertEquals('ver', gitflow.get_prefix('versiontag'))

    @copy_from_fixture('partly_inited')
    def test_gitflow_init_config_with_partly_inited(self):
        gitflow = GitFlow(self.repo).init()

        # Already set in fixture, shouldn't change
        self.assertEquals('production', gitflow.master_name())
        self.assertEquals('f-', gitflow.get_prefix('feature'))

        # Implicit defaults
        self.assertEquals('develop', gitflow.develop_name())
        self.assertEquals('origin', gitflow.origin_name())
        self.assertEquals('release/', gitflow.get_prefix('release'))
        self.assertEquals('hotfix/', gitflow.get_prefix('hotfix'))
        self.assertEquals('support/', gitflow.get_prefix('support'))
        self.assertEquals('', gitflow.get_prefix('versiontag'))


    @copy_from_fixture('sample_repo')
    def test_gitflow_init_keeps_active_branch_if_develop_already_existed(self):
        active_branch = self.repo.active_branch.name
        gitflow = GitFlow(self.repo).init()
        self.assertEqual(gitflow.repo.active_branch.name, active_branch)

    def test_gitflow_init_checkout_develop_if_newly_created(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        self.assertEqual(gitflow.repo.active_branch.name, 'develop')

    @copy_from_fixture('sample_repo')
    def test_gitflow_init_creates_no_extra_commits(self):
        all_commits_before_init = all_commits(self.repo)
        gitflow = GitFlow(self.repo).init()
        all_commits_after_init = all_commits(self.repo)
        self.assertEquals(all_commits_before_init, all_commits_after_init)

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_init_cloned_creates_no_extra_commits(self):
        all_commits_before_init = all_commits(self.repo)
        gitflow = GitFlow(self.repo).init()
        all_commits_after_init = all_commits(self.repo)
        self.assertEquals(all_commits_before_init, all_commits_after_init)

    @copy_from_fixture('sample_repo')
    def test_gitflow_init_creates_no_extra_branches(self):
        heads_before_init = [h.name for h in self.repo.heads]
        gitflow = GitFlow(self.repo).init()
        heads_after_init = [h.name for h in self.repo.heads]
        self.assertItemsEqual(heads_before_init, heads_after_init)

    def test_gitflow_init_creates_initial_commit(self):
        repo = create_git_repo(self)
        all_commits_before_init = all_commits(repo)
        gitflow = GitFlow(repo).init()
        all_commits_after_init = all_commits(repo)
        self.assertNotEquals(all_commits_before_init, all_commits_after_init)
        self.assertEquals('Initial commit', repo.heads.master.commit.message)

    def test_gitflow_init_creates_branches(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        self.assertItemsEqual(['master', 'develop'],
                gitflow.branch_names())

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_init_cloned_creates_master_and_develop(self):
        heads_before_init = [h.name for h in self.repo.heads]
        self.assertNotIn('stable', heads_before_init)
        self.assertNotIn('devel', heads_before_init)
        gitflow = GitFlow(self.repo).init()
        heads_after_init = [h.name for h in self.repo.heads]
        self.assertIn('stable', heads_after_init)
        self.assertIn('devel', heads_after_init)

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_init_cloned_creates_no_custom_master_and_develop(self):
        heads_before_init = [h.name for h in self.repo.heads]
        self.assertNotIn('foo', heads_before_init)
        self.assertNotIn('bar', heads_before_init)
        gitflow = GitFlow(self.repo)
        self.assertRaises(NotImplementedError,
                          gitflow.init, master='foo', develop='bar')

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_init_cloned_creates_branches_from_counterpart(self):
        remote =  GitFlow(self.remote)
        rmc0 = remote.master().commit
        rdc0 = remote.develop().commit

        gitflow = GitFlow(self.repo).init()
        mc0 = gitflow.master().commit
        dc0 = gitflow.develop().commit

        # local and remote heads must be the same
        self.assertEqual(rmc0, mc0)
        self.assertEqual(rdc0, dc0)
        self.assertTrue(gitflow.master().tracking_branch())
        self.assertTrue(gitflow.develop().tracking_branch())
        self.assertEqual(gitflow.master().tracking_branch().name, 'my-remote/stable')
        self.assertEqual(gitflow.develop().tracking_branch().name, 'my-remote/devel')


    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_init_cloned_creates_no_extra_banches(self):
        heads_before_init = [h.name for h in self.repo.heads]
        heads_before_init.sort()
        gitflow = GitFlow(self.repo).init()
        heads_after_init = [h.name for h in self.repo.heads]
        heads_after_init.remove('stable')
        heads_after_init.remove('devel')
        self.assertItemsEqual(heads_before_init, heads_after_init)

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_init_cloned_checkout_develop_if_newly_created(self):
        gitflow = GitFlow(self.repo).init()
        self.assertEqual(gitflow.repo.active_branch.name, 'devel')

    @copy_from_fixture('partly_inited')
    def test_gitflow_force_reinit_partly_inited(self):
        gitflow = GitFlow(self.repo)
        gitflow.init(force_defaults=True)

        # Implicit defaults
        self.assertEquals('develop', gitflow.develop_name())
        self.assertEquals('origin', gitflow.origin_name())
        self.assertEquals('release/', gitflow.get_prefix('release'))
        self.assertEquals('hotfix/', gitflow.get_prefix('hotfix'))
        self.assertEquals('support/', gitflow.get_prefix('support'))
        self.assertEquals('', gitflow.get_prefix('versiontag'))

        # Explicitly forced back to defaults
        self.assertEquals('master', gitflow.master_name())
        self.assertEquals('feature/', gitflow.get_prefix('feature'))


class TestGitFlowTag(TestCase):

    @copy_from_fixture('sample_repo')
    def test_gitflow_tag_without_message(self):
        gitflow = GitFlow(self.repo).init()
        self.assertNotIn('some-tag', self.repo.tags)
        commit = self.repo.head.commit
        gitflow.tag('some-tag', commit)
        self.assertIn('some-tag', self.repo.tags)
        tagref = self.repo.tags['some-tag']
        self.assertEqual(tagref.commit, commit)
        self.assertEqual(tagref.name, 'some-tag')
        # if there is no message, tagref.tag is None
        self.assertEqual(tagref.tag, None)

    @copy_from_fixture('sample_repo')
    def test_gitflow_tag_with_message(self):
        gitflow = GitFlow(self.repo).init()
        self.assertNotIn('some-tag', self.repo.tags)
        commit = self.repo.head.commit
        gitflow.tag('some-tag', commit, 'This is my tag')
        self.assertIn('some-tag', self.repo.tags)
        tagref = self.repo.tags['some-tag']
        self.assertEqual(tagref.commit, commit)
        self.assertEqual(tagref.name, 'some-tag')
        # if there is no message, tagref.tag is None
        self.assertNotEqual(tagref.tag, None)

        tag = tagref.tag
        self.assertEqual(tag.message, 'This is my tag')
        self.assertEqual(tag.tag, 'some-tag')
        self.assertEqual(tag.object, commit)

    @set_gnupg_home
    @copy_from_fixture('sample_repo')
    def test_gitflow_tag_signed(self):
        gitflow = GitFlow(self.repo).init()
        # need to the the signing key via config
        gitflow.set('user.signingkey', 'Dummy Key for Gitflow testing')
        commit = self.repo.head.commit
        gitflow.tag('some-tag', commit, 'This is my tag', sign=True)
        tag = self.repo.tags['some-tag'].tag
        expected = ['This is my tag', '-----BEGIN PGP SIGNATURE-----']
        self.assertEqual(tag.message.splitlines()[:2], expected)
        self.assertEqual(tag.tag, 'some-tag')
        self.assertEqual(tag.object, commit)

    @set_gnupg_home
    @copy_from_fixture('sample_repo')
    def test_gitflow_tag_signed_with_key(self):
        gitflow = GitFlow(self.repo).init()
        commit = self.repo.head.commit
        gitflow.tag('some-tag', commit, 'This is my tag', sign=True,
                    signingkey='Dummy Key for Gitflow testing')
        tag = self.repo.tags['some-tag'].tag
        expected = ['This is my tag', '-----BEGIN PGP SIGNATURE-----']
        self.assertEqual(tag.message.splitlines()[:2], expected)
        self.assertEqual(tag.tag, 'some-tag')
        self.assertEqual(tag.object, commit)


    # :todo: test-cases for must_be_uptodate
    # :todo: test-cases for branch_names(remote=True)
    # :todo: test-cases for list (one per BranchManager)

class TestGitFlowMerges(TestCase):

    @copy_from_fixture('sample_repo')
    def test_gitflow_is_merged_into(self):
        gitflow = GitFlow(self.repo).init()

        # feat/even is ahead of devel
        self.assertTrue(gitflow.is_merged_into('devel', 'feat/even'))
        self.assertFalse(gitflow.is_merged_into('feat/even', 'devel'))
        # devel as a symbolic ref
        self.assertFalse(gitflow.is_merged_into('feat/even',
                                                self.repo.refs['devel']))
        # feat/even a symbolic ref
        self.assertFalse(gitflow.is_merged_into(self.repo.refs['feat/even'],
                                                'devel'))
        # HEAD
        self.assertFalse(gitflow.is_merged_into('HEAD', 'devel'))
        self.assertFalse(gitflow.is_merged_into(self.repo.head, 'devel'))

    @copy_from_fixture('sample_repo')
    def test_gitflow_is_merged_into_non_existing_source(self):
        gitflow = GitFlow(self.repo).init()
        self.assertRaisesRegexp(BadObjectError, 'feat/ever',
                          gitflow.is_merged_into ,'feat/ever', 'devel')

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_is_merged_into_remote(self):
        gitflow = GitFlow(self.repo).init()

        # devel is behind feat/even
        self.assertTrue(gitflow.is_merged_into(
            'devel',
            'remotes/my-remote/feat/even'))
        self.assertTrue(gitflow.is_merged_into(
            'devel',
            gitflow.origin().refs['devel']))
        self.assertTrue(gitflow.is_merged_into(
            gitflow.origin().refs['devel'],
            'remotes/my-remote/feat/even'))
        self.assertTrue(gitflow.is_merged_into(
            gitflow.origin().refs['devel'],
            gitflow.origin().refs['devel']))

        # feat/even is ahead of devel
        self.assertFalse(gitflow.is_merged_into(
            'feat/recursion',
            'devel'))
        self.assertFalse(gitflow.is_merged_into(
            'remotes/my-remote/feat/recursion',
            'devel'))

        self.assertFalse(gitflow.is_merged_into(
            'feat/recursion',
            gitflow.origin().refs['devel']))
        self.assertFalse(gitflow.is_merged_into(
            'remotes/my-remote/feat/recursion',
            gitflow.origin().refs['devel']))

    #:todo: test-case is_merged_into_remote with remote branch beeing ahead
    #       of corresponding local branch

    @copy_from_fixture('sample_repo')
    def test_has_no_merge_conflict(self):
        gitflow = GitFlow(self.repo).init()
        gitflow.require_no_merge_conflict()

    @copy_from_fixture('sample_repo')
    def test_has_merge_conflict(self):
        gitflow = GitFlow(self.repo).init()
        repo = gitflow.repo
        repo.refs['devel'].checkout()
        repo.git.merge('feat/recursion')
        # the next merge creates the merge conflict
        self.assertRaises(GitCommandError,
                          repo.git.merge, 'feat/even')
        self.assertRaises(MergeConflict, gitflow.require_no_merge_conflict)

    # :todo: test-cases for compare_branches
    # :todo: test-cases for require_branches_equal


class TestGitFlowCheckout(TestCase):
    @copy_from_fixture('sample_repo')
    def test_gitflow_nameprefix_or_current_defaults_to_current(self):
        gitflow = GitFlow(self.repo).init()
        active_branch = self.repo.active_branch
        gitflow.checkout('feature', 'even')
        self.assertNotEqual(gitflow.repo.active_branch.name, active_branch)
        self.assertEqual(gitflow.repo.active_branch.name, 'feat/even')


class TestGitFlowBranches(TestCase):

    #-- nameprefix_or_current

    @copy_from_fixture('sample_repo')
    def test_gitflow_nameprefix_or_current_defaults_to_current(self):
        gitflow = GitFlow(self.repo).init()
        # gitflow.init checks out `devel` branch :-(
        self.repo.branches['feat/recursion'].checkout()
        self.assertEqual(gitflow.nameprefix_or_current('feature', ''),
                         'recursion')

    @copy_from_fixture('sample_repo')
    def test_gitflow_nameprefix_or_current_on_other_branch_type_raises_error(self):
        gitflow = GitFlow(self.repo).init()
        # gitflow.init checks out `devel` branch :-(
        self.repo.branches['feat/recursion'].checkout()
        self.assertRaises(NoSuchBranchError,
                          gitflow.nameprefix_or_current, 'release', '')

    @copy_from_fixture('sample_repo')
    def test_gitflow_nameprefix_or_current_expands_prefix(self):
        gitflow = GitFlow(self.repo).init()
        # gitflow.init checks out `devel` branch :-(
        self.repo.branches['feat/recursion'].checkout()
        self.assertEqual(gitflow.nameprefix_or_current('feature', 'e'), 'even')

    @copy_from_fixture('sample_repo')
    def test_gitflow_nameprefix_or_current_returns_name(self):
        gitflow = GitFlow(self.repo).init()
        # gitflow.init checks out `devel` branch :-(
        self.repo.branches['feat/recursion'].checkout()
        self.assertEqual('even',
            gitflow.name_or_current('feature', 'even'))

    #-- name_or_current

    @copy_from_fixture('sample_repo')
    def test_gitflow_name_or_current_defaults_to_current(self):
        gitflow = GitFlow(self.repo).init()
        # gitflow.init checks out `devel` branch :-(
        self.repo.branches['feat/recursion'].checkout()
        self.assertEqual(gitflow.name_or_current('feature', ''),
                         'recursion')

    @copy_from_fixture('sample_repo')
    def test_gitflow_name_or_current_on_other_branch_type_raises_error(self):
        gitflow = GitFlow(self.repo).init()
        # gitflow.init checks out `devel` branch :-(
        self.repo.branches['feat/recursion'].checkout()
        self.assertRaises(NoSuchBranchError,
                          gitflow.name_or_current, 'release', '')

    @copy_from_fixture('sample_repo')
    def test_gitflow_name_or_current_for_nonexisting_name_raises_error(self):
        gitflow = GitFlow(self.repo).init()
        # gitflow.init checks out `devel` branch :-(
        self.repo.branches['feat/recursion'].checkout()
        self.assertRaises(NoSuchBranchError,
                          gitflow.name_or_current, 'feature', 'xxxx')

    @copy_from_fixture('sample_repo')
    def test_gitflow_name_or_current_returns_name(self):
        gitflow = GitFlow(self.repo).init()
        # gitflow.init checks out `devel` branch :-(
        self.repo.branches['feat/recursion'].checkout()
        self.assertEqual('even',
            gitflow.name_or_current('feature', 'even'))
        self.assertEqual('xxxx',
            gitflow.name_or_current('feature', 'xxxx', must_exist=False))


class TestGitFlowCommandCreate(TestCase):

    # more tests are done in test_branches.py

    def test_create_in_new_sandbox(self):
        sandbox = create_sandbox(self)
        gitflow = GitFlow(sandbox).init()
        gitflow.create('feature', 'wow-feature', base=None, fetch=False)
        self.assertIn('feature/wow-feature', gitflow.repo.branches)

class TestGitFlowCommandFinish(TestCase):

    # more tests are done in test_branches.py

    def test_finish_in_new_sandbox(self):
        sandbox = create_sandbox(self)
        gitflow = GitFlow(sandbox).init()
        gitflow.create('feature', 'wow-feature', base=None, fetch=False)
        self.assertEqual(gitflow.repo.active_branch.name, 'feature/wow-feature')
        fake_commit(gitflow.repo, 'Yet another commit')
        gitflow.finish('feature', 'wow-feature', False, False, False, False, None)
        self.assertNotIn('feature/wow-feature', gitflow.repo.branches)

    def test_finish_in_new_sandbox_without_commit(self):
        sandbox = create_sandbox(self)
        gitflow = GitFlow(sandbox).init()
        gitflow.create('feature', 'wow-feature', base=None, fetch=False)
        gitflow.finish('feature', 'wow-feature', False, False, False, False, None)
        self.assertNotIn('feature/wow-feature', gitflow.repo.branches)


class TestGitFlowCommandTrack(TestCase):

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_track_creates_tracking_branch(self):
        gitflow = GitFlow(self.repo).init()
        gitflow.track('feature', 'even')
        self.assertEqual(self.repo.active_branch.name, 'feat/even')
        self.assertTrue(self.repo.active_branch.tracking_branch())
        self.assertEqual(self.repo.refs['feat/even'].tracking_branch(),
                         gitflow.origin().refs['feat/even'])

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_track_existing_branch_raises_error(self):
        gitflow = GitFlow(self.repo).init()
        self.assertRaises(BranchExistsError,
                          gitflow.track, 'feature', 'recursion')

    # :todo: more test-cases for GitFlow.track()


class TestGitFlowCommandRebase(TestCase):

    @copy_from_fixture('sample_repo')
    def test_gitflow_rebase(self):
        gitflow = GitFlow(self.repo).init()
        dc0 = self.repo.refs['devel'].commit
        fc0 = self.repo.refs['feat/even'].commit
        b0 = self.repo.git.merge_base(dc0, fc0)

        gitflow.develop().checkout()
        fake_commit(self.repo, 'A commit on devel')
        dc1 = self.repo.refs['devel'].commit
        b1 = self.repo.git.merge_base(dc1, fc0)
        # commit advances `devel`
        self.assertNotEqual(dc0, dc1)
        # merge base is still the same
        self.assertEqual(b0, b1)

        gitflow.rebase('feature', 'even', interactive=False)

        fc1 = self.repo.refs['feat/even'].commit
        b2 = self.repo.git.merge_base('devel', 'feat/even')
        # rebase advances `feat/even`
        self.assertNotEqual(fc0, fc1)
        # merge base is now new `devel` head
        self.assertEqual(b2, dc1.hexsha)


class TestGitFlowCommandPull(TestCase):

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_pull_creates_non_tracking_branch(self):
        gitflow = GitFlow(self.repo).init()
        gitflow.pull('feature', 'my-remote', 'even')
        self.assertEqual(self.repo.active_branch.name, 'feat/even')
        self.assertEqual(self.repo.active_branch.tracking_branch(), None)

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_pull_while_on_other_branchtype_is_allowed(self):
        gitflow = GitFlow(self.repo).init()
        # activate some hotfix branch
        new_branch = self.repo.create_head('hf-dummy', 'stable')
        new_branch.checkout()
        gitflow.pull('feature', 'my-remote', 'even')

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_pull_while_on_same_branchtype_raises_error(self):
        gitflow = GitFlow(self.repo).init()
        # activate some feature branch
        new_branch = self.repo.create_head('feat/something', 'stable')
        new_branch.checkout()
        # try to pull another feature branch
        self.assertRaisesRegexp(
            SystemExit, "To avoid unintended merges, git-flow aborted.",
            gitflow.pull, 'feature', 'my-remote', 'my-name-is-irrelevant')


    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_pull_existing_branch_creates_non_tracking_branch(self):
        gitflow = GitFlow(self.repo).init()
        # create local branch based on first commit
        new_branch = self.repo.create_head('feat/even', 'stable')
        new_branch.checkout()
        gitflow.pull('feature', 'my-remote', 'even')
        self.assertEqual(self.repo.active_branch.name, 'feat/even')
        self.assertEqual(self.repo.active_branch.tracking_branch(), None)

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_pull_existing_branch_while_on_other_branchtype_raises_error(self):
        gitflow = GitFlow(self.repo).init()
        # create local branch based on first commit
        new_branch = self.repo.create_head('feat/even', 'stable')
        self.assertRaisesRegexp(
            SystemExit, "To avoid unintended merges, git-flow aborted.",
            gitflow.pull, 'feature', 'my-remote', 'even')

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_pull_existing_branch_while_on_same_branchtype_raises_error(self):
        gitflow = GitFlow(self.repo).init()
        # create local branch based on first commit
        new_branch = self.repo.create_head('feat/even', 'stable')
        # activate some feature branch
        new_branch = self.repo.create_head('feat/something', 'stable')
        new_branch.checkout()
        self.assertRaisesRegexp(
            SystemExit, "To avoid unintended merges, git-flow aborted.",
            gitflow.pull, 'feature', 'my-remote', 'even')


    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_pull_non_existing_feature_raises_error(self):
        all_remote_commits_before_change = all_commits(self.remote)
        gitflow = GitFlow(self.repo).init()
        self.assertRaisesRegexp(
            GitCommandError, "Couldn't find remote ref ",
            gitflow.pull, 'feature', 'my-remote', 'i-am-not-here')

    # :todo: pull changed and test if new commit is really pulled
    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_pull_really_pulls(self):
        gitflow = GitFlow(self.repo).init()
        self.remote.heads['feat/even'].checkout()
        change = fake_commit(self.remote, "Another commit")
        self.assertNotIn(change, all_commits(self.repo))
        gitflow.pull('feature', 'my-remote', 'even')
        self.assertIn(change, all_commits(self.repo))

    # :todo: pull_requires_clean_working_tree


class TestGitFlowCommandPublish(TestCase):

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_publish_creates_remote_branch(self):
        gitflow = GitFlow(self.repo).init()
        gitflow.create('feature', 'circular', 'devel', fetch=False)
        gitflow.publish('feature', 'circular')
        self.assertIn('feat/circular', self.remote.branches)

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_publish_creates_sets_tracking_branch(self):
        gitflow = GitFlow(self.repo).init()
        gitflow.create('feature', 'circular', 'devel', fetch=False)
        gitflow.publish('feature', 'circular')

        self.assertTrue(self.repo.branches['feat/circular'].tracking_branch())
        self.assertTrue(self.repo.branches['feat/circular'].tracking_branch().name,
                        'my-remote/feat/circular')

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_publish_really_pushes(self):
        gitflow = GitFlow(self.repo).init()
        gitflow.create('feature', 'circular', 'devel', fetch=False)
        change = fake_commit(self.repo, "Another commit")
        all_local_commits = all_commits(self.repo)
        self.assertIn(change, all_local_commits)
        gitflow.publish('feature', 'circular')

        all_remote_commits = all_commits(self.remote)
        self.assertEqual(all_remote_commits, all_remote_commits)
        self.assertIn(change, all_remote_commits)

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_publish_non_existing_branch_raises_error(self):
        gitflow = GitFlow(self.repo).init()
        self.assertRaises(NoSuchBranchError,
                          gitflow.publish, 'feature', 'new-feature')

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_publish_branch_existing_remote_raises_error(self):
        gitflow = GitFlow(self.repo).init()
        self.assertRaises(NoSuchBranchError,
                          gitflow.publish, 'feature', 'even')

    # :todo: publish_requires_clean_working_tree


class TestGitFlowCommandDiff(TestCase):

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_publish_creates_remote_branch(self):
        gitflow = GitFlow(self.repo).init()
        orig_stdout = sys.stdout
        sys.stdout = StringIO.StringIO()
        gitflow.diff('feature', 'recursion')
        diff = sys.stdout.getvalue()
        sys.stdout = orig_stdout
        difflines = diff.splitlines()
        matchlines = [
            'diff --git a/odd.py b/odd.py',
            'index 607a269..8a0c7ff 100644',
            '--- a/odd.py',
            '+++ b/odd.py',
            ]
        self.assertEqual(difflines[:len(matchlines)], matchlines)


class TestGitFlowBranchManagement(TestCase):

    # Branch type detection
    def test_detect_branch_types(self):
        create_git_repo(self)
        gitflow = GitFlow()

        # The types that "ship" with git-flow
        self.assertIn('feature', gitflow.managers)
        self.assertIn('release', gitflow.managers)
        self.assertIn('hotfix', gitflow.managers)
        self.assertIn('support', gitflow.managers)

    def test_detect_custom_branch_types(self):
        create_git_repo(self)
        # Declare a custom branch type inline
        class FooBarManager(BranchManager):
            identifier = 'foobar'
            DEFAULT_PREFIX = 'xyz/'

        gitflow = GitFlow()
        self.assertIn('foobar', gitflow.managers)


    # Branch creation
    def test_create_branches(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        gitflow.create('feature', 'foo', None, fetch=False)
        self.assertIn('feature/foo',
                [h.name for h in gitflow.repo.branches])
        gitflow.create('release', '1.0', None, fetch=False)
        self.assertIn('release/1.0',
                [h.name for h in gitflow.repo.branches])

    def _test_create_branches_from_alt_base(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        gitflow.create('feature', 'foo', 'master', fetch=False)
        self.assertIn('feature/foo',
                [h.name for h in gitflow.repo.branches])
        gitflow.repo.index.commit('Foo')
        gitflow.create('release', '1.0', 'feature/foo', fetch=False)
        self.assertIn('release/1.0',
                [h.name for h in gitflow.repo.branches])


    """
    Use case:

    $ git flow init
    $ git flow feature start foo
    $ git flow status
      develop: 4826bdf
      master: 4826bdf
    * feature/foo: 7c8928a
    $ git commit -m 'foo'
    $ git commit -m 'bar'
    $ git flow feature start bar
    $ git commit -m 'qux'
    $ git flow feature finish foo
    $ git flow undo        # new!
    $ git flow feature finish bar
    There were merge conflicts, resolve them now!
    $ git flow abort       # new!

    """

