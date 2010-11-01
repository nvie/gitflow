from unittest2 import TestCase, skip
from git import GitCommandError
from gitflow.core import GitFlow
from gitflow.branches import BranchManager, FeatureBranchManager, \
        ReleaseBranchManager, HotfixBranchManager
from tests.helpers import sandboxed_git_repo, copy_from_fixture


class FooBranchManager(BranchManager):
    """
    A fictious Foo branch, used to test Branch functionality, but we need
    a concrete class, since Branch is an "abstract" class.
    """
    identifier = 'abc'
    prefix = 'xyz/'


class TestGenericBranchManager(TestCase):
    @sandboxed_git_repo
    def test_default_prefix(self):
        gitflow = GitFlow()
        fb = FooBranchManager(gitflow)
        self.assertEquals('xyz/', fb.prefix)

    @sandboxed_git_repo
    def test_explicit_prefix(self):
        gitflow = GitFlow()
        fb = FooBranchManager(gitflow, 'xyz-')
        self.assertEquals('xyz-', fb.prefix)

    @sandboxed_git_repo
    def test_explicit_empty_prefix(self):
        gitflow = GitFlow()
        fb = FooBranchManager(gitflow, '')
        self.assertEquals('', fb.prefix)


class TestFeatureBranchManager(TestCase):
    # Helper methods
    def fake_commit(self, message):
        with open('newfile.py', 'a') as f:
            f.write('This is a dummy change.\n')
        self.repo.index.add(['newfile.py'])
        self.repo.index.commit(message)


    # Tests
    @copy_from_fixture('sample_repo')
    def test_list(self):
        gitflow = GitFlow()
        mgr = FeatureBranchManager(gitflow)
        expected = ['feature/even', 'feature/recursion']
        self.assertItemsEqual(expected, [b.name for b in mgr.list()])

    @sandboxed_git_repo
    def test_list_empty_repo(self):
        gitflow = GitFlow()
        mgr = FeatureBranchManager(gitflow)
        self.assertItemsEqual([], mgr.list())

    @copy_from_fixture('sample_repo')
    def test_list_without_matching_prefix(self):
        gitflow = GitFlow()
        mgr = FeatureBranchManager(gitflow, 'fb-')
        expected = []
        self.assertItemsEqual(expected, [b.name for b in mgr.list()])


    @sandboxed_git_repo
    def test_create_new_feature_branch(self):
        gitflow = GitFlow()
        gitflow.init()
        mgr = FeatureBranchManager(gitflow)
        self.assertEqual(0, len(mgr.list()))
        new_branch = mgr.create('foo')
        self.assertEqual(1, len(mgr.list()))
        self.assertEqual('feature/foo', mgr.list()[0].name)
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['develop'].commit)

    @copy_from_fixture('sample_repo')
    def test_create_new_feature_from_alt_base(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)

        new_branch = mgr.create('foo', 'feature/even')
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['feature/even'].commit)

    @sandboxed_git_repo
    def test_create_existing_feature_branch_yields_raises_error(self):
        gitflow = GitFlow()
        gitflow.init()
        mgr = FeatureBranchManager(gitflow)
        mgr.create('foo')
        self.assertRaises(GitCommandError, mgr.create, 'foo')

    @copy_from_fixture('sample_repo')
    def test_create_feature_changes_active_branch(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)

        self.assertEquals('feature/recursion', self.repo.active_branch.name)
        mgr.create('foo')
        self.assertEquals('feature/foo', self.repo.active_branch.name)

    @copy_from_fixture('dirty_sample_repo')
    def test_create_feature_raises_error_if_local_changes_would_be_overwritten(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)
        self.assertRaises(GitCommandError,
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
        self.assertNotIn('feature/foo', [b.name for b in self.repo.branches])


    @copy_from_fixture('sample_repo')
    def test_delete_already_merged_feature(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)

        self.assertEquals(2, len(mgr.list()))
        mgr.create('foo')
        self.fake_commit('Dummy commit #1')
        self.fake_commit('Dummy commit #2')
        mgr.merge('foo', 'develop')

        self.assertEquals(3, len(mgr.list()))
        mgr.delete('foo')
        self.assertEquals(2, len(mgr.list()))
        self.assertNotIn('feature/foo', [b.name for b in mgr.list()])

    @copy_from_fixture('sample_repo')
    def test_delete_feature_with_commits_raises_error(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)

        self.assertEquals(2, len(mgr.list()))
        mgr.create('foo')
        f = open('newfile.py', 'w')
        f.write('This is a dummy file.\n')
        f.close()
        self.repo.index.add(['newfile.py'])
        self.repo.index.commit('A commit on the feature branch.')

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
        f = open('newfile.py', 'w')
        f.write('This is a dummy file.\n')
        f.close()
        self.repo.index.add(['newfile.py'])
        self.repo.index.commit('A commit on the feature branch.')

        gitflow.develop().checkout()
        self.assertEquals(3, len(mgr.list()))
        mgr.delete('foo', force=True)
        self.assertEquals(2, len(mgr.list()))
        self.assertNotIn('feature/foo', [b.name for b in self.repo.branches])

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


    @sandboxed_git_repo
    def test_merge_feature_with_multiple_commits(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()
        mgr = FeatureBranchManager(gitflow)

        old_develop_commit = gitflow.develop().commit

        mgr.create('newstuff')
        self.fake_commit('Foo commit')
        self.fake_commit('Bar commit')
        self.fake_commit('Qux commit')
        mgr.merge('newstuff', 'develop')

        develop_commit = gitflow.develop().commit

        # Assert merge commit has been made
        self.assertEqual(2, len(develop_commit.parents))
        self.assertEqual(
                "Merge branch 'feature/newstuff' into develop\n",
                develop_commit.message)

        # Assert develop branch advanced
        self.assertNotEqual(old_develop_commit, develop_commit)

    @sandboxed_git_repo
    def test_merge_feature_with_single_commit(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()
        mgr = FeatureBranchManager(gitflow)

        old_develop_commit = gitflow.develop().commit

        mgr.create('newstuff')
        self.fake_commit('Foo commit')
        mgr.merge('newstuff', 'develop')

        develop_commit = gitflow.develop().commit

        # Assert no merge commit has been made
        self.assertEqual(1, len(develop_commit.parents))
        self.assertEqual('Foo commit', develop_commit.message)

        # Assert develop branch advanced
        self.assertNotEqual(old_develop_commit, develop_commit)

    @sandboxed_git_repo
    def test_merge_feature_without_commits(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()
        mgr = FeatureBranchManager(gitflow)

        old_develop_commit = gitflow.develop().commit

        mgr.create('newstuff')
        mgr.merge('newstuff', 'develop')

        develop_commit = gitflow.develop().commit

        # Assert the develop tip is unchanged by the merge
        self.assertEqual(old_develop_commit, develop_commit)


class TestReleaseBranchManager(TestCase):
    @sandboxed_git_repo
    def test_empty_repo_has_no_releases(self):
        gitflow = GitFlow()
        mgr = ReleaseBranchManager(gitflow)
        self.assertItemsEqual([], mgr.list())

    @copy_from_fixture('release')
    def test_list(self):
        gitflow = GitFlow()
        mgr = ReleaseBranchManager(gitflow)
        expected = ['release/1.0']
        self.assertItemsEqual(expected, [b.name for b in mgr.list()])

    @copy_from_fixture('release')
    def test_list_without_matching_prefix(self):
        gitflow = GitFlow()
        mgr = ReleaseBranchManager(gitflow, 'rel-')
        expected = []
        self.assertItemsEqual(expected, [b.name for b in mgr.list()])

    @sandboxed_git_repo
    def test_create_new_release_branch(self):
        gitflow = GitFlow()
        gitflow.init()
        mgr = ReleaseBranchManager(gitflow)
        self.assertEqual(0, len(mgr.list()))
        new_branch = mgr.create('3.14-beta5')
        self.assertEqual(1, len(mgr.list()))
        self.assertEqual('release/3.14-beta5', mgr.list()[0].name)
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['develop'].commit)

    @copy_from_fixture('sample_repo')
    def test_create_new_release_from_alt_base(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)

        new_branch = mgr.create('1.0',
                'c8b6deac7ef94f078a426d52c0b1fb3e1221133c')  # develop~1
        self.assertEqual(new_branch.commit.hexsha,
                'c8b6deac7ef94f078a426d52c0b1fb3e1221133c')

    @sandboxed_git_repo
    def test_create_existing_release_branch_yields_raises_error(self):
        gitflow = GitFlow()
        gitflow.init()
        mgr = ReleaseBranchManager(gitflow)
        mgr.create('1.0')
        self.assertRaises(GitCommandError, mgr.create, '1.0')

    @sandboxed_git_repo
    def test_create_release_changes_active_branch(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()
        mgr = ReleaseBranchManager(gitflow)

        self.assertEquals('master', self.repo.active_branch.name)
        mgr.create('1.0')
        self.assertEquals('release/1.0', self.repo.active_branch.name)

    @copy_from_fixture('dirty_sample_repo')
    def test_create_release_raises_error_if_local_changes_would_be_overwritten(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)
        self.assertRaises(GitCommandError,
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

    @copy_from_fixture('sample_repo')
    def test_delete_release(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)

        self.assertEquals(0, len(mgr.list()))
        mgr.create('1.0')
        gitflow.develop().checkout()
        self.assertEquals(1, len(mgr.list()))
        mgr.delete('1.0')
        self.assertEquals(0, len(mgr.list()))
        self.assertNotIn('release/1.0', [b.name for b in mgr.list()])

    @copy_from_fixture('sample_repo')
    def test_cannot_delete_current_release(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)
        mgr.create('1.0').checkout()
        self.assertRaisesRegexp(GitCommandError,
                'Cannot delete the branch .* which you are currently on',
                mgr.delete, '1.0')

    @copy_from_fixture('sample_repo')
    def test_cannot_delete_non_existing_release(self):
        gitflow = GitFlow(self.repo)
        mgr = ReleaseBranchManager(gitflow)
        self.assertRaisesRegexp(GitCommandError, 'branch .* not found',
                mgr.delete, 'nonexisting')


class TestHotfixBranchManager(TestCase):
    @sandboxed_git_repo
    def test_create_new_hotfix_branch(self):
        gitflow = GitFlow()
        gitflow.init()
        mgr = HotfixBranchManager(gitflow)
        self.assertEqual(0, len(mgr.list()))
        new_branch = mgr.create('3.14-beta5')
        self.assertEqual(1, len(mgr.list()))
        self.assertEqual('hotfix/3.14-beta5', mgr.list()[0].name)

    @copy_from_fixture('sample_repo')
    def test_hotfixes_branch_off_from_master(self):
        gitflow = GitFlow()
        mgr = HotfixBranchManager(gitflow)
        new_branch = mgr.create('3.14-beta5')
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['master'].commit)

    @copy_from_fixture('sample_repo')
    def test_create_new_release_from_alt_base(self):
        gitflow = GitFlow(self.repo)
        mgr = HotfixBranchManager(gitflow)
        new_branch = mgr.create('1.0',
                'c8b6deac7ef94f078a426d52c0b1fb3e1221133c')  # develop~1
        self.assertEqual(new_branch.commit.hexsha,
                'c8b6deac7ef94f078a426d52c0b1fb3e1221133c')

