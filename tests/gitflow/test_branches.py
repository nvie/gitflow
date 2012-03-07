#
# This file is part of `gitflow`.
# Copyright (c) 2010-2011 Vincent Driessen
# Copyright (c) 2012 Hartmut Goebel
# Distributed under a BSD-like license. For full terms see the file LICENSE.txt
#

from unittest2 import TestCase

from git import GitCommandError

from gitflow.core import GitFlow, NoSuchRemoteError
from gitflow.branches import (
    BranchManager, FeatureBranchManager,
    ReleaseBranchManager, HotfixBranchManager, SupportBranchManager,
    PrefixNotUniqueError, NoSuchBranchError, BranchExistsError,
    BranchTypeExistsError, WorkdirIsDirtyError)

from tests.helpers import (copy_from_fixture, remote_clone_from_fixture,
                           fake_commit, all_commits, set_gnupg_home)
from tests.helpers.factory import create_git_repo

__copyright__ = "2010-2011 Vincent Driessen; 2012 Hartmut Goebel"
__license__ = "BSD"

class DummyBranchManager(BranchManager):
    """
    A fictious Dummy branch, used to test Branch functionality, but we need
    a concrete class, since Branch is an "abstract" class.
    """
    identifier = 'abc'
    DEFAULT_PREFIX = 'xyz/'


class TestAbstractBranchManager(TestCase):
    def __prep_explicit_prefix(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        fb = DummyBranchManager(gitflow, 'xyz-')
        return repo, fb

    def __prep_explicit_empty_prefix(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        fb = DummyBranchManager(gitflow, '')
        return repo, fb

    def test_default_prefix(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        fb = DummyBranchManager(gitflow)
        self.assertEquals('xyz/', fb.prefix)

    def test_explicit_prefix(self):
        repo, fb = self.__prep_explicit_prefix()
        self.assertEquals('xyz-', fb.prefix)

    def test_explicit_empty_prefix(self):
        repo, fb = self.__prep_explicit_empty_prefix()
        self.assertEquals('', fb.prefix)

    def test_shorten(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        fb = DummyBranchManager(gitflow)
        self.assertEquals('foo', fb.shorten('xyz/foo'))
        self.assertEquals('feature/foo', fb.shorten('feature/foo'))

    def test_full_name(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        fb = DummyBranchManager(gitflow)
        self.assertEquals('xyz/foo', fb.full_name('foo'))
        self.assertEquals('xyz/feature/foo', fb.full_name('feature/foo'))

    def test_explicit_prefix_shorten(self):
        repo, fb = self.__prep_explicit_prefix()
        self.assertEquals('foo', fb.shorten('xyz-foo'))
        self.assertEquals('xyz/foo', fb.shorten('xyz/foo'))
        self.assertEquals('feature/foo', fb.shorten('feature/foo'))

    def test_explicit_empty_prefix_shorten(self):
        repo, fb = self.__prep_explicit_empty_prefix()
        self.assertEquals('xyz-foo', fb.shorten('xyz-foo'))
        self.assertEquals('xyz/foo', fb.shorten('xyz/foo'))
        self.assertEquals('feature/foo', fb.shorten('feature/foo'))

    def test_explicit_prefix_full_name(self):
        repo, fb = self.__prep_explicit_prefix()
        self.assertEquals('xyz-foo', fb.full_name('foo'))
        self.assertEquals('xyz-xyz/foo', fb.full_name('xyz/foo'))
        self.assertEquals('xyz-feature/foo', fb.full_name('feature/foo'))

    def test_explicit_empty_prefix_full_name(self):
        repo, fb = self.__prep_explicit_empty_prefix()
        self.assertEquals('foo', fb.full_name('foo'))
        self.assertEquals('xyz-foo', fb.full_name('xyz-foo'))
        self.assertEquals('xyz/foo', fb.full_name('xyz/foo'))
        self.assertEquals('feature/foo', fb.full_name('feature/foo'))

    # :todo: test-cases for merge with conflicts


class TestFeatureBranchManager(TestCase):

    def test_defined_members(self):
        # must define at least these members
        members = vars(FeatureBranchManager).keys()
        self.assertIn('DEFAULT_PREFIX', members)
        self.assertIn('identifier', members)

    def test_empty_repo_has_no_features(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        mgr = FeatureBranchManager(gitflow)
        self.assertItemsEqual([], mgr.list())

    @copy_from_fixture('sample_repo')
    def test_shorten(self):
        gitflow = GitFlow(self.repo)
        fb = FeatureBranchManager(gitflow)
        self.assertEquals('foo', fb.shorten('feat/foo'))
        self.assertEquals('feature/foo', fb.shorten('feature/foo'))

    @copy_from_fixture('sample_repo')
    def test_full_name(self):
        gitflow = GitFlow(self.repo)
        fb = FeatureBranchManager(gitflow)
        self.assertEquals('feat/foo', fb.full_name('foo'))
        self.assertEquals('feat/feature/foo', fb.full_name('feature/foo'))

    @copy_from_fixture('sample_repo')
    def test_list(self):
        gitflow = GitFlow()
        mgr = FeatureBranchManager(gitflow)
        expected = ['feat/even', 'feat/recursion']
        self.assertItemsEqual(expected, [b.name for b in mgr.list()])

    @copy_from_fixture('sample_repo')
    def test_list_without_matching_prefix(self):
        gitflow = GitFlow()
        mgr = FeatureBranchManager(gitflow, 'fb-')
        expected = []
        self.assertItemsEqual(expected, [b.name for b in mgr.list()])


    @copy_from_fixture('sample_repo')
    def test_by_nameprefix(self):
        gitflow = GitFlow()
        mgr = FeatureBranchManager(gitflow)
        self.assertEquals('feat/even', mgr.by_name_prefix('e').name)
        self.assertEquals('feat/recursion', mgr.by_name_prefix('re').name)

    @copy_from_fixture('sample_repo')
    def test_by_nameprefix_not_unique_enough(self):
        gitflow = GitFlow()
        mgr = FeatureBranchManager(gitflow)
        mgr.create('rescue')
        self.assertRaises(PrefixNotUniqueError, mgr.by_name_prefix, 're')
        self.assertRaises(NoSuchBranchError, mgr.by_name_prefix, 'nonexisting')

    #--- create ---

    def test_create_new_feature_branch(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        mgr = FeatureBranchManager(gitflow)
        self.assertEqual(0, len(mgr.list()))
        new_branch = mgr.create('foo')
        self.assertEqual(1, len(mgr.list()))
        self.assertEqual('feature/foo', mgr.list()[0].name)
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['develop'].commit)

    @copy_from_fixture('sample_repo')
    def test_create_new_feature_branch_non_default_prefix(self):
        gitflow = GitFlow(self.repo).init()
        mgr = FeatureBranchManager(gitflow)
        new_branch = mgr.create('foo')
        self.assertEqual(new_branch.name, 'feat/foo')
        self.assertIn('feat/foo', [b.name for b in mgr.list()])
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['devel'].commit)

    @copy_from_fixture('sample_repo')
    def test_create_new_feature_from_alt_base(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)

        new_branch = mgr.create('foo', 'feat/even')
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['feat/even'].commit)

    def test_feature_branch_origin(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        mgr = FeatureBranchManager(gitflow)
        new_branch = mgr.create('foobar')
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['develop'].commit)

    def test_create_existing_feature_branch_raises_error(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        mgr = FeatureBranchManager(gitflow)
        mgr.create('foo')
        self.assertRaises(BranchExistsError, mgr.create, 'foo')

    def test_create_feature_branch_fetch_without_remote_raises_error(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        mgr = FeatureBranchManager(gitflow)
        self.assertRaises(NoSuchRemoteError, mgr.create, 'foo', fetch=True)

    @remote_clone_from_fixture('sample_repo')
    def test_create_feature_from_remote_branch(self):
        remote_branch = self.remote.refs['feat/even']
        rfc0 = remote_branch.commit
        gitflow = GitFlow(self.repo).init()
        mgr = FeatureBranchManager(gitflow)
        mgr.create('even')
        branch = self.repo.active_branch
        self.assertEqual(branch.name, 'feat/even')
        self.assertEqual(branch.commit, rfc0)
        # must be a tracking branch
        self.assertTrue(branch.tracking_branch())
        self.assertEqual(branch.tracking_branch().name, 'my-remote/feat/even')

    @remote_clone_from_fixture('sample_repo')
    def test_create_feature_from_remote_branch_with_develop_behind(self):
        # If BranchManager.create() uses `update`, this test-case has
        # to be adopted, since since `update` change the cloned repo.
        rfc0 = self.remote.refs['feat/even'].commit
        rdc0 = self.remote.refs['devel'].commit
        # add a commit to remote develop branch
        self.remote.refs['devel'].checkout()
        change = fake_commit(self.remote, "Yet another develop commit.")

        gitflow = GitFlow(self.repo).init()
        mgr = FeatureBranchManager(gitflow)
        mgr.create('even')
        # must not advance develop nor feat/even
        self.assertEqual(self.repo.refs['feat/even'].commit, rfc0)
        self.assertEqual(self.repo.refs['devel'].commit, rdc0)
        # change must not be in local repo
        self.assertNotIn(change, all_commits(self.repo))

    @remote_clone_from_fixture('sample_repo')
    def test_create_feature_from_remote_branch_behind(self):
        # If BranchManager.create() uses `update`, this test-case has
        # to be adopted, since since `update` change the cloned repo.
        rfc0 = self.remote.refs['feat/even'].commit
        # add a commit to remote feat/even branch
        self.remote.refs['feat/even'].checkout()
        change = fake_commit(self.remote, "Yet another even commit.")

        gitflow = GitFlow(self.repo).init()
        mgr = FeatureBranchManager(gitflow)
        mgr.create('even')
        # does not advance feat/even, since create() uses `fetch`, not `update`
        self.assertEqual(self.repo.refs['feat/even'].commit, rfc0)
        # change must not be in local repo, since create() uses `fetch`, not `update`
        self.assertNotIn(change, all_commits(self.repo))


    @remote_clone_from_fixture('sample_repo')
    def test_create_feature_fetch_from_remote_branch_behind_really_fetches(self):
        rfc0 = self.remote.refs['feat/even'].commit
        # add a commit to remote feat/even branch
        self.remote.refs['feat/even'].checkout()
        change = fake_commit(self.remote, "Yet another even commit.")

        gitflow = GitFlow(self.repo).init()
        mgr = FeatureBranchManager(gitflow)
        mgr.create('even', fetch=True)
        # must not advance feat/even
        self.assertEqual(self.repo.refs['feat/even'].commit, rfc0)
        # change must nor be in local repo
        self.assertNotIn(change, all_commits(self.repo))


    @copy_from_fixture('sample_repo')
    def test_create_feature_changes_active_branch(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)

        self.assertEquals('feat/recursion', self.repo.active_branch.name)
        mgr.create('foo')
        self.assertEquals('feat/foo', self.repo.active_branch.name)

    @copy_from_fixture('dirty_sample_repo')
    def test_create_feature_raises_error_if_local_changes_would_be_overwritten(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)
        self.assertRaisesRegexp(WorkdirIsDirtyError, 'checked in.*not committed',
                mgr.create, 'foo')

    @copy_from_fixture('dirty_sample_repo')
    def test_create_feature_changes_active_branch_even_if_dirty_but_without_conflicts(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)

        # In this fixture, odd.py contains changes that would be overwritten.
        # Since we don't want to test this here, we revert all local changes in
        # odd.py, but leave the local changes in README.txt.  These changes
        # won't be overwritten by the merge, so git-flow should be able to
        # create a new feature branch if Git can do this
        self.repo.index.reset(index=True, working_tree=True, paths=['odd.py'])
        mgr.create('foo')
        self.assertIn('feature/foo', [b.name for b in mgr.iter()])

    # :todo: test-cases for create with base not on develop
    # :todo: test-cases for create with remote base not on develop

    #---- delete ---

    @copy_from_fixture('sample_repo')
    def test_delete_feature_without_commits(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)

        self.assertEquals(2, len(mgr.list()))
        mgr.create('foo')
        gitflow.develop().checkout()
        self.assertEquals(3, len(mgr.list()))
        mgr.delete('foo')
        self.assertEquals(2, len(mgr.list()))
        self.assertNotIn('feat/foo', [b.name for b in self.repo.branches])


    @copy_from_fixture('sample_repo')
    def test_delete_already_merged_feature(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)

        self.assertEquals(2, len(mgr.list()))
        mgr.create('foo')
        fake_commit(self.repo, 'Dummy commit #1')
        fake_commit(self.repo, 'Dummy commit #2')
        mgr.merge('foo', 'devel')

        self.assertEquals(3, len(mgr.list()))
        mgr.delete('foo')
        self.assertEquals(2, len(mgr.list()))
        self.assertNotIn('feat/foo', [b.name for b in mgr.list()])

    @copy_from_fixture('sample_repo')
    def test_delete_feature_with_commits_raises_error(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)

        self.assertEquals(2, len(mgr.list()))
        mgr.create('foo')
        fake_commit(self.repo, 'A commit on the feature branch.', append=False)
        gitflow.develop().checkout()
        self.assertEquals(3, len(mgr.list()))
        self.assertRaisesRegexp(GitCommandError,
                'The branch .* is not fully merged',
                mgr.delete, 'foo')

    @copy_from_fixture('sample_repo')
    def test_delete_feature_with_commits_forcefully(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)

        self.assertEquals(2, len(mgr.list()))
        mgr.create('foo')
        fake_commit(self.repo, 'A commit on the feature branch.', append=False)
        gitflow.develop().checkout()
        self.assertEquals(3, len(mgr.list()))
        mgr.delete('foo', force=True)
        self.assertEquals(2, len(mgr.list()))
        self.assertNotIn('feat/foo', [b.name for b in self.repo.branches])

    @copy_from_fixture('sample_repo')
    def test_delete_current_feature_raises_error(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)
        mgr.create('foo').checkout()
        self.assertRaisesRegexp(GitCommandError,
                'Cannot delete the branch .* which you are currently on',
                mgr.delete, 'foo')

    @copy_from_fixture('sample_repo')
    def test_delete_non_existing_feature_raises_error(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)
        self.assertRaisesRegexp(GitCommandError, 'branch .* not found',
                mgr.delete, 'nonexisting')

    #--- merge ---

    @copy_from_fixture('sample_repo')
    def test_merge_feature_with_multiple_commits(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)

        dc0 = gitflow.develop().commit
        mgr.merge('even', 'devel')
        dc1 = gitflow.develop().commit

        # Assert merge commit has been made
        self.assertEqual(2, len(dc1.parents))
        self.assertEqual(
                "Merge branch 'feat/even' into devel\n",
                dc1.message)

        # Assert develop branch advanced
        self.assertNotEqual(dc0, dc1)
        # Assert the target-branch is active
        self.assertEqual(gitflow.repo.active_branch.name, 'devel')

    @copy_from_fixture('sample_repo')
    def test_merge_feature_with_single_commit(self):
        gitflow = GitFlow(self.repo).init()
        mgr = FeatureBranchManager(gitflow)

        dc0 = gitflow.develop().commit
        mgr.merge('recursion', 'devel')
        dc1 = gitflow.develop().commit

        # Assert no merge commit has been made
        self.assertEqual(1, len(dc1.parents))
        self.assertEqual('Made the definition of odd recursive.\n',
                dc1.message)

        # Assert develop branch advanced
        self.assertNotEqual(dc0, dc1)
        # Assert the target-branch is active
        self.assertEqual(gitflow.repo.active_branch.name, 'devel')

    def test_merge_feature_without_commits(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        mgr = FeatureBranchManager(gitflow)

        dc0 = gitflow.develop().commit
        mgr.create('newstuff')
        mgr.merge('newstuff', 'develop')
        dc1 = gitflow.develop().commit

        # Assert the develop tip is unchanged by the merge
        self.assertEqual(dc0, dc1)
        # Assert the target-branch is active
        self.assertEqual(gitflow.repo.active_branch.name, 'develop')

    #--- finish ---

    @copy_from_fixture('sample_repo')
    def test_finish_feature(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)

        mc0 = gitflow.master().commit
        dc0 = gitflow.develop().commit
        mgr.finish('even')
        mc1 = gitflow.master().commit
        dc1 = gitflow.develop().commit

        # Feature finishes don't advance master, but develop
        self.assertEqual(mc0, mc1)
        self.assertNotEqual(dc0, dc1)

        # Finishing removes the feature branch
        self.assertNotIn('feat/even',
                [b.name for b in self.repo.branches])

        # Merge commit message
        self.assertEquals('Finished feature even.\n', dc1.message)

    @copy_from_fixture('sample_repo')
    def test_finish_feature_keep(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)
        mgr.finish('even', keep=True)
        # feature branch still exists
        self.assertIn('feat/even',
                [b.name for b in self.repo.branches])


    @remote_clone_from_fixture('sample_repo')
    def test_finish_feature_on_unpulled_branch_raises_error(self):
        # branch exists on remote but was not pulled prior to finish
        gitflow = GitFlow(self.repo).init()
        mgr = FeatureBranchManager(gitflow)
        self.assertRaises(NoSuchBranchError, mgr.finish, 'even', push=True)


    @remote_clone_from_fixture('sample_repo')
    def test_finish_feature_push(self):
        remote =  GitFlow(self.remote).init()
        gitflow = GitFlow(self.repo).init()

        rmc0 = remote.master().commit
        rdc0 = remote.develop().commit
        mc0 = gitflow.master().commit
        dc0 = gitflow.develop().commit

        mgr = FeatureBranchManager(gitflow)
        mgr.create('even')
        mgr.finish('even', push=True)

        rmc1 = remote.master().commit
        rdc1 = remote.develop().commit
        mc1 = gitflow.master().commit
        dc1 = gitflow.develop().commit

        # Feature finishes don't advance remote master, but remote develop
        self.assertEqual(rmc0, rmc1)
        self.assertNotEqual(rdc0, rdc1)
        self.assertEqual(mc0, mc1)
        self.assertNotEqual(dc0, dc1)

        # local and remote heads must be the same again
        self.assertEqual(rmc1, mc1)
        self.assertEqual(rdc1, dc1)

        # Finishing removes the local and the remote feature branch
        self.assertNotIn('feat/even',
                [b.name for b in self.repo.branches])
        self.assertNotIn('feat/even',
                [b.name for b in self.remote.branches])

        # Merge commit message
        self.assertEquals('Finished feature even.\n', rdc1.message)


    @remote_clone_from_fixture('sample_repo')
    def test_finish_feature_push_keep(self):
        gitflow = GitFlow(self.repo).init()
        mgr = FeatureBranchManager(gitflow)
        mgr.create('even')
        mgr.finish('even', push=True, keep=True)

        # Finishing removes the local and the remote feature branch
        self.assertIn('feat/even',
                [b.name for b in self.repo.branches])
        self.assertIn('feat/even',
                [b.name for b in self.remote.branches])

    # :todo: test-cases for finish with merge-conflicts for both develop
    # :todo: test-cases for finish with rebase
    # :todo: test-cases for finish with rebase-conflicts for both develop

class TestReleaseBranchManager(TestCase):

    def test_defined_members(self):
        # must define at least these members
        members = vars(ReleaseBranchManager).keys()
        self.assertIn('DEFAULT_PREFIX', members)
        self.assertIn('identifier', members)

    @copy_from_fixture('sample_repo')
    def test_shorten(self):
        gitflow = GitFlow(self.repo)
        fb = ReleaseBranchManager(gitflow)
        self.assertEquals('foo', fb.shorten('rel/foo'))
        self.assertEquals('release/foo', fb.shorten('release/foo'))

    @copy_from_fixture('sample_repo')
    def test_full_name(self):
        gitflow = GitFlow(self.repo)
        fb = ReleaseBranchManager(gitflow)
        self.assertEquals('rel/foo', fb.full_name('foo'))
        self.assertEquals('rel/release/foo', fb.full_name('release/foo'))

    def test_empty_repo_has_no_releases(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        mgr = ReleaseBranchManager(gitflow)
        self.assertItemsEqual([], mgr.list())

    @copy_from_fixture('release')
    def test_list(self):
        gitflow = GitFlow()
        mgr = ReleaseBranchManager(gitflow)
        expected = ['rel/1.0']
        self.assertItemsEqual(expected, [b.name for b in mgr.list()])

    @copy_from_fixture('release')
    def test_list_without_matching_prefix(self):
        gitflow = GitFlow()
        mgr = ReleaseBranchManager(gitflow, 'rel-')
        expected = []
        self.assertItemsEqual(expected, [b.name for b in mgr.list()])

    @copy_from_fixture('release')
    def test_by_nameprefix(self):
        gitflow = GitFlow()
        mgr = ReleaseBranchManager(gitflow)
        self.assertEquals('rel/1.0', mgr.by_name_prefix('1').name)

    @copy_from_fixture('release')
    def test_by_nameprefix_not_unique_enough(self):
        gitflow = GitFlow()
        mgr = ReleaseBranchManager(gitflow)
        # Create branch without manager since manager enforces there
        # is a single release branch.
        self.repo.create_head('rel/1.1', 'HEAD')
        self.assertRaises(PrefixNotUniqueError, mgr.by_name_prefix, '1.')
        self.assertRaises(NoSuchBranchError, mgr.by_name_prefix, 'nonexisting')

    #--- create ---

    def test_create_new_release_branch(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        mgr = ReleaseBranchManager(gitflow)
        self.assertEqual(0, len(mgr.list()))
        new_branch = mgr.create('3.14-beta5')
        self.assertEqual(1, len(mgr.list()))
        self.assertEqual('release/3.14-beta5', mgr.list()[0].name)
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['develop'].commit)

    @copy_from_fixture('sample_repo')
    def test_create_new_release_branch_non_default_prefix(self):
        gitflow = GitFlow(self.repo).init()
        mgr = ReleaseBranchManager(gitflow)
        new_branch = mgr.create('3.14-beta5')
        self.assertEqual(new_branch.name, 'rel/3.14-beta5')
        self.assertIn('rel/3.14-beta5', [b.name for b in mgr.list()])
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['devel'].commit)

    @copy_from_fixture('sample_repo')
    def test_create_new_release_from_alt_base(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)

        new_branch = mgr.create('1.0',
                'c8b6deac7ef94f078a426d52c0b1fb3e1221133c')  # devel~1
        self.assertEqual(new_branch.commit.hexsha,
                'c8b6deac7ef94f078a426d52c0b1fb3e1221133c')

    def test_release_branch_origin(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        mgr = ReleaseBranchManager(gitflow)
        new_branch = mgr.create('1.1')
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['develop'].commit)

    def test_create_existing_release_branch_raises_error(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        mgr = ReleaseBranchManager(gitflow)
        mgr.create('1.0')
        self.assertRaises(BranchTypeExistsError, mgr.create, '1.0')

    def test_create_release_branch_fetch_without_remote_raises_error(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        mgr = ReleaseBranchManager(gitflow)
        self.assertRaises(NoSuchRemoteError, mgr.create, 'foo', fetch=True)

    @remote_clone_from_fixture('release')
    def test_create_release_from_remote_branch(self):
        remote_branch = self.remote.refs['rel/1.0']
        rfc0 = remote_branch.commit
        gitflow = GitFlow(self.repo).init()
        mgr = ReleaseBranchManager(gitflow)
        mgr.create('1.0')
        branch = self.repo.active_branch
        self.assertEqual(branch.name, 'rel/1.0')
        self.assertEqual(branch.commit, rfc0)
        # must be a tracking branch
        self.assertTrue(branch.tracking_branch())
        self.assertEqual(branch.tracking_branch().name, 'my-remote/rel/1.0')

    @remote_clone_from_fixture('release')
    def test_create_release_from_remote_branch_with_develop_behind(self):
        # If BranchManager.create() uses `update`, this test-case has
        # to be adopted, since `update` changes the cloned repo.
        rfc0 = self.remote.refs['rel/1.0'].commit
        rdc0 = self.remote.refs['devel'].commit
        # add a commit to remote develop branch
        self.remote.refs['devel'].checkout()
        change = fake_commit(self.remote, "Yet another develop commit.")

        gitflow = GitFlow(self.repo).init()
        mgr = ReleaseBranchManager(gitflow)
        mgr.create('1.0')
        # must not advance develop nor rel/1.0
        self.assertEqual(self.repo.refs['rel/1.0'].commit, rfc0)
        self.assertEqual(self.repo.refs['devel'].commit, rdc0)
        # change must not be in local repo
        self.assertNotIn(change, all_commits(self.repo))

    @remote_clone_from_fixture('release')
    def test_create_release_from_remote_branch_behind(self):
        # If BranchManager.create() uses `update`, this test-case has
        # to be adopted, since since `update` change the cloned repo.
        rfc0 = self.remote.refs['rel/1.0'].commit
        # add a commit to remote rel/1.0 branch
        self.remote.refs['rel/1.0'].checkout()
        change = fake_commit(self.remote, "Yet another 1.0 commit.")

        gitflow = GitFlow(self.repo).init()
        mgr = ReleaseBranchManager(gitflow)
        mgr.create('1.0')
        # does not advance rel/1.0, since create() uses `fetch`, not `update`
        self.assertEqual(self.repo.refs['rel/1.0'].commit, rfc0)
        # change must not be in local repo, since create() uses `fetch`, not `update`
        self.assertNotIn(change, all_commits(self.repo))


    @remote_clone_from_fixture('release')
    def test_create_release_fetch_from_remote_branch_behind_really_fetches(self):
        rfc0 = self.remote.refs['rel/1.0'].commit
        # add a commit to remote rel/1.0 branch
        self.remote.refs['rel/1.0'].checkout()
        change = fake_commit(self.remote, "Yet another 1.0 commit.")

        gitflow = GitFlow(self.repo).init()
        mgr = ReleaseBranchManager(gitflow)
        mgr.create('1.0', fetch=True)
        # must not advance rel/1.0
        self.assertEqual(self.repo.refs['rel/1.0'].commit, rfc0)
        # change must nor be in local repo
        self.assertNotIn(change, all_commits(self.repo))

    def test_create_release_changes_active_branch(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        mgr = ReleaseBranchManager(gitflow)

        self.assertEquals('develop', repo.active_branch.name)
        mgr.create('1.0')
        self.assertEquals('release/1.0', repo.active_branch.name)

    @copy_from_fixture('dirty_sample_repo')
    def test_create_release_raises_error_if_local_changes_would_be_overwritten(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)
        self.assertRaisesRegexp(WorkdirIsDirtyError, 'checked in.*not committed',
                mgr.create, '1.0')

    @copy_from_fixture('dirty_sample_repo')
    def test_create_release_changes_active_branch_even_if_dirty_but_without_conflicts(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)

        # In this fixture, odd.py contains changes that would be overwritten.
        # Since we don't want to test this here, we revert all local changes in
        # odd.py, but leave the local changes in README.txt.  These changes
        # won't be overwritten by the merge, so git-flow should be able to
        # create a new release branch if Git can do this
        self.repo.index.reset(index=True, working_tree=True, paths=['odd.py'])
        mgr.create('1.0')
        self.assertIn('release/1.0', [b.name for b in mgr.iter()])

    # :todo: test-cases for create with base not on develop
    # :todo: test-cases for create with remote base not on develop

    #---- delete ---

    @copy_from_fixture('sample_repo')
    def test_delete_release_without_commits(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)

        self.assertEquals(0, len(mgr.list()))
        mgr.create('1.0')
        gitflow.develop().checkout()
        self.assertEquals(1, len(mgr.list()))
        mgr.delete('1.0')
        self.assertEquals(0, len(mgr.list()))
        self.assertNotIn('rel/1.0', [b.name for b in mgr.list()])

    @copy_from_fixture('sample_repo')
    def test_delete_already_merged_release(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)

        self.assertEquals(0, len(mgr.list()))
        mgr.create('0.7')
        fake_commit(self.repo, 'Dummy commit #1')
        fake_commit(self.repo, 'Dummy commit #2')
        mgr.merge('0.7', 'devel')

        self.assertEquals(1, len(mgr.list()))
        mgr.delete('0.7')
        self.assertEquals(0, len(mgr.list()))
        self.assertNotIn('rel/0.7', [b.name for b in mgr.list()])

    @copy_from_fixture('sample_repo')
    def test_delete_release_with_commits_raises_error(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)

        self.assertEquals(0, len(mgr.list()))
        mgr.create('0.7')
        fake_commit(self.repo, 'A commit on the release branch.', append=False)
        gitflow.develop().checkout()
        self.assertEquals(1, len(mgr.list()))
        self.assertRaisesRegexp(GitCommandError,
                'The branch .* is not fully merged',
                mgr.delete, '0.7')

    @copy_from_fixture('sample_repo')
    def test_delete_release_with_commits_forcefully(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)

        self.assertEquals(0, len(mgr.list()))
        mgr.create('0.7')
        fake_commit(self.repo, 'A commit on the release branch.', append=False)
        gitflow.develop().checkout()
        self.assertEquals(1, len(mgr.list()))
        mgr.delete('0.7', force=True)
        self.assertEquals(0, len(mgr.list()))
        self.assertNotIn('rel/0.7', [b.name for b in self.repo.branches])

    @copy_from_fixture('sample_repo')
    def test_delete_current_release_raises_error(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)
        mgr.create('1.0').checkout()
        self.assertRaisesRegexp(GitCommandError,
                'Cannot delete the branch .* which you are currently on',
                mgr.delete, '1.0')

    @copy_from_fixture('sample_repo')
    def test_delete_non_existing_release_raises_error(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)
        self.assertRaisesRegexp(GitCommandError, 'branch .* not found',
                mgr.delete, 'nonexisting')

    #--- merge ---
    # No need to test merge for ReleaseBranchManager since it is the
    # same as for FeatureBranch Manager

    #--- finish ---

    @copy_from_fixture('release')
    def test_finish_release(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)

        mc0 = gitflow.master().commit
        dc0 = gitflow.develop().commit
        mgr.finish('1.0')
        mc1 = gitflow.master().commit
        dc1 = gitflow.develop().commit

        # Release finishes advance both master and develop
        self.assertNotEqual(mc0, mc1)
        self.assertNotEqual(dc0, dc1)
        # master is merged back to develop
        self.assertIn(mc1, dc1.parents)

        # Finishing removes the release branch
        self.assertNotIn('rel/1.0',
                [b.name for b in self.repo.branches])

        # Merge commit message
        self.assertEquals('Finished release 1.0.\n', dc1.message)
        self.assertEquals('Finished release 1.0.\n', mc1.message)


    @copy_from_fixture('release')
    def test_finish_release_keep(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)
        mgr.finish('1.0', keep=True)
        # release branch still exists
        self.assertIn('rel/1.0',
                [b.name for b in self.repo.branches])

    @copy_from_fixture('release')
    def test_finish_release_tag(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)
        taginfo = dict(
            message = 'Tagging version 1.0'
            )
        mgr.finish('1.0', tagging_info=taginfo)
        mc1 = gitflow.master().commit
        dc1 = gitflow.develop().commit
        # master is merged back to develop
        self.assertIn(mc1, dc1.parents)
        # tag exists
        self.assertIn('v1.0', self.repo.tags)
        self.assertEqual(self.repo.tags['v1.0'].commit, mc1)
        # tag message
        self.assertEqual(self.repo.tags['v1.0'].tag.message,
                         'Tagging version 1.0')

    @set_gnupg_home
    @copy_from_fixture('release')
    def test_finish_release_tag_sign(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)
        taginfo = dict(
            message = 'Tagging version 1.0',
            signingkey = 'Dummy Key for Gitflow testing',
            )
        mgr.finish('1.0', tagging_info=taginfo)
        # tag message
        tag = self.repo.tags['v1.0'].tag
        self.assertIn('-----BEGIN PGP SIGNATURE-----', tag.message)


    @remote_clone_from_fixture('release')
    def test_finish_release_on_unpulled_branch_raises_error(self):
        # branch exists on remote but was not pulled prior to finish
        gitflow = GitFlow(self.repo).init()
        mgr = ReleaseBranchManager(gitflow)
        self.assertRaises(NoSuchBranchError, mgr.finish, '1.0', push=True)


    @remote_clone_from_fixture('release')
    def test_finish_release_push(self):
        remote =  GitFlow(self.remote).init()
        # Since remote is no bare repo, checkout some branch untouched
        # by this operation. :fixme: find better solution
        self.remote.heads['feat/even'].checkout()
        gitflow = GitFlow(self.repo).init()

        rmc0 = remote.master().commit
        rdc0 = remote.develop().commit
        mc0 = gitflow.master().commit
        dc0 = gitflow.develop().commit

        mgr = ReleaseBranchManager(gitflow)
        mgr.create('1.0')
        mgr.finish('1.0', push=True)
        rmc1 = remote.master().commit
        rdc1 = remote.develop().commit
        mc1 = gitflow.master().commit
        dc1 = gitflow.develop().commit

        # Release finishes advances master and develop both local and remote
        self.assertNotEqual(rmc0, rmc1)
        self.assertNotEqual(rdc0, rdc1)
        self.assertNotEqual(mc0, mc1)
        self.assertNotEqual(dc0, dc1)

        # local and remote heads must be the same again
        self.assertEqual(rmc1, mc1)
        self.assertEqual(rdc1, dc1)

        # Finishing removes the local and the remote release branch
        self.assertNotIn('rel/1.0',
                [b.name for b in self.repo.branches])
        self.assertNotIn('rel/1.0',
                [b.name for b in self.remote.branches])


        # Merge commit message
        self.assertEquals('Finished release 1.0.\n', rdc1.message)


    @remote_clone_from_fixture('release')
    def test_finish_release_push_keep(self):
        # Since remote is no bare repo, checkout some branch untouched
        # by this operation. :fixme: find better solution
        self.remote.heads['feat/even'].checkout()
        gitflow = GitFlow(self.repo).init()
        mgr = ReleaseBranchManager(gitflow)
        mgr.create('1.0')
        mgr.finish('1.0', push=True, keep=True)

        # release branch still exists local and remote
        self.assertIn('rel/1.0',
                [b.name for b in self.repo.branches])
        self.assertIn('rel/1.0',
                [b.name for b in self.remote.branches])


    @remote_clone_from_fixture('release')
    def test_finish_release_tag_push(self):
        # Since remote is no bare repo, checkout some branch untouched
        # by this operation. :fixme: find better solution
        self.remote.heads['feat/even'].checkout()
        gitflow = GitFlow(self.repo).init()

        mgr = ReleaseBranchManager(gitflow)
        mgr.create('1.0')
        taginfo = dict(
            message = 'Tagging version 1.0'
            )
        mgr.finish('1.0', push=True, tagging_info=taginfo)
        mc1 = gitflow.master().commit
        # remote tag exists
        self.assertIn('v1.0', self.remote.tags)
        self.assertEqual(self.remote.tags['v1.0'].commit, mc1)
        # tag message
        self.assertEqual(self.remote.tags['v1.0'].tag.message,
                         'Tagging version 1.0')


    @set_gnupg_home
    @remote_clone_from_fixture('release')
    def test_finish_release_tag_sign_push(self):
        # Since remote is no bare repo, checkout some branch untouched
        # by this operation. :fixme: find better solution
        self.remote.heads['feat/even'].checkout()
        gitflow = GitFlow(self.repo).init()

        mgr = ReleaseBranchManager(gitflow)
        mgr.create('1.0')
        taginfo = dict(
            message = 'Tagging version 1.0',
            signingkey = 'Dummy Key for Gitflow testing',
            )
        mgr.finish('1.0', push=True, tagging_info=taginfo)
        # tag message
        tag = self.remote.tags['v1.0'].tag
        self.assertIn('-----BEGIN PGP SIGNATURE-----', tag.message)


    # :todo: test-cases for finish with merge-conflicts for both master and develop
    def test_finish_release_rebase(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        mgr = ReleaseBranchManager(gitflow)
        mgr.create('1.0')
        self.assertRaisesRegexp(
            AssertionError, "does not make any sense",
            mgr.finish, '1.0', rebase=True)


class TestHotfixBranchManager(TestCase):

    def test_defined_members(self):
        members = vars(HotfixBranchManager).keys()
        self.assertEqual(members,
                         ['DEFAULT_PREFIX', '__module__',
                          'identifier', 'default_base', '__doc__'])

    @copy_from_fixture('sample_repo')
    def test_shorten(self):
        gitflow = GitFlow(self.repo)
        fb = HotfixBranchManager(gitflow)
        self.assertEquals('foo', fb.shorten('hf/foo'))
        self.assertEquals('hotfix/foo', fb.shorten('hotfix/foo'))

    @copy_from_fixture('sample_repo')
    def test_full_name(self):
        gitflow = GitFlow(self.repo)
        fb = HotfixBranchManager(gitflow)
        self.assertEquals('hf/foo', fb.full_name('foo'))
        self.assertEquals('hf/hotfix/foo', fb.full_name('hotfix/foo'))

    def test_empty_repo_has_no_hotfixes(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        mgr = HotfixBranchManager(gitflow)
        self.assertItemsEqual([], mgr.list())

    def test_create_new_hotfix_branch(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        mgr = HotfixBranchManager(gitflow)
        self.assertEqual(0, len(mgr.list()))
        new_branch = mgr.create('1.2.3')
        self.assertEqual(1, len(mgr.list()))
        self.assertEqual('hotfix/1.2.3', mgr.list()[0].name)
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['master'].commit)

    @copy_from_fixture('sample_repo')
    def test_create_new_hotfix_branch_non_default_prefix(self):
        gitflow = GitFlow(self.repo).init()
        mgr = HotfixBranchManager(gitflow)
        new_branch = mgr.create('1.2.3')
        self.assertEqual('hf/1.2.3', mgr.list()[0].name)
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['stable'].commit)

    # :todo: test-cases for create with base not on master
    # :todo: test-cases for create with remote base not on master

    @copy_from_fixture('sample_repo')
    def test_hotfix_branch_origin(self):
        gitflow = GitFlow()
        mgr = HotfixBranchManager(gitflow)
        new_branch = mgr.create('3.14-beta5')
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['stable'].commit)

    @copy_from_fixture('sample_repo')
    def test_finish_hotfix(self):
        gitflow = GitFlow(self.repo)
        mgr = HotfixBranchManager(gitflow)
        mgr.create('1.2.3')
        fake_commit(self.repo, 'Bogus commit')
        fake_commit(self.repo, 'Foo commit')
        fake_commit(self.repo, 'Fake commit')
        fake_commit(self.repo, 'Dummy commit')

        mc0 = gitflow.master().commit
        dc0 = gitflow.develop().commit
        mgr.finish('1.2.3')
        mc1 = gitflow.master().commit
        dc1 = gitflow.develop().commit

        # Hotfix finishes advance both master and develop
        self.assertNotEqual(mc0, mc1)
        self.assertNotEqual(dc0, dc1)

        # Finishing removes the hotfix branch
        self.assertNotIn('hf/1.2.3',
                [b.name for b in self.repo.branches])

        # Merge commit message
        self.assertEquals('Finished hotfix 1.2.3.\n', dc1.message)


class TestSupportBranchManager(TestCase):

    def test_defined_members(self):
        # must define at least these members
        members = vars(SupportBranchManager).keys()
        self.assertIn('DEFAULT_PREFIX', members)
        self.assertIn('identifier', members)
        self.assertIn('default_base',  members)

    @copy_from_fixture('sample_repo')
    def test_shorten(self):
        gitflow = GitFlow(self.repo)
        fb = SupportBranchManager(gitflow)
        self.assertEquals('foo', fb.shorten('supp/foo'))
        self.assertEquals('support/foo', fb.shorten('support/foo'))

    @copy_from_fixture('sample_repo')
    def test_full_name(self):
        gitflow = GitFlow(self.repo)
        fb = SupportBranchManager(gitflow)
        self.assertEquals('supp/foo', fb.full_name('foo'))
        self.assertEquals('supp/support/foo', fb.full_name('support/foo'))

    def test_empty_repo_has_no_support(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        mgr = SupportBranchManager(gitflow)
        self.assertItemsEqual([], mgr.list())

    def test_create_new_support_branch(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        mgr = SupportBranchManager(gitflow)
        self.assertEqual(0, len(mgr.list()))
        new_branch = mgr.create('1.x')
        self.assertEqual(1, len(mgr.list()))
        self.assertEqual('support/1.x', mgr.list()[0].name)
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['master'].commit)

    @copy_from_fixture('sample_repo')
    def test_create_new_support_branch_non_default_prefix(self):
        gitflow = GitFlow(self.repo).init()
        mgr = SupportBranchManager(gitflow)
        new_branch = mgr.create('1.x')
        self.assertEqual('supp/1.x', mgr.list()[0].name)
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['stable'].commit)

    @copy_from_fixture('sample_repo')
    def test_support_branch_origin(self):
        gitflow = GitFlow()
        mgr = SupportBranchManager(gitflow)
        new_branch = mgr.create('legacy')
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['stable'].commit)

    # :todo: test-cases for create with base not on master
    # :todo: test-cases for create with remote base not on master

    def test_support_branches_cannot_be_finished(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo).init()
        mgr = SupportBranchManager(gitflow)
        mgr.create('1.x')
        self.assertRaises(NotImplementedError, mgr.finish, '1.x')

