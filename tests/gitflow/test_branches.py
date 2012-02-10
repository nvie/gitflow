from unittest2 import TestCase
from git import GitCommandError
from gitflow.core import GitFlow
from gitflow.branches import BranchManager, FeatureBranchManager, \
        ReleaseBranchManager, HotfixBranchManager, SupportBranchManager, \
        PrefixNotUniqueError, NoSuchBranchError, BranchExistsError
from tests.helpers import copy_from_fixture
from tests.helpers.factory import create_git_repo


def fake_commit(repo, message):
    f = open('newfile.py', 'a')
    try:
        f.write('This is a dummy change.\n')
    finally:
        f.close()
    repo.index.add(['newfile.py'])
    repo.index.commit(message)


class DummyBranchManager(BranchManager):
    """
    A fictious Dummy branch, used to test Branch functionality, but we need
    a concrete class, since Branch is an "abstract" class.
    """
    identifier = 'abc'
    prefix = 'xyz/'


class TestAbstractBranchManager(TestCase):
    def test_default_prefix(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        fb = DummyBranchManager(gitflow)
        self.assertEquals('xyz/', fb.prefix)

    def test_explicit_prefix(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        fb = DummyBranchManager(gitflow, 'xyz-')
        self.assertEquals('xyz-', fb.prefix)

    def test_explicit_empty_prefix(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        fb = DummyBranchManager(gitflow, '')
        self.assertEquals('', fb.prefix)

    def test_shorten(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        fb = DummyBranchManager(gitflow)
        self.assertEquals('foo', fb.shorten('xyz/foo'))
        self.assertEquals('feature/foo', fb.shorten('feature/foo'))


class TestFeatureBranchManager(TestCase):
    @copy_from_fixture('sample_repo')
    def test_list(self):
        gitflow = GitFlow()
        mgr = FeatureBranchManager(gitflow)
        expected = ['feature/even', 'feature/recursion']
        self.assertItemsEqual(expected, [b.name for b in mgr.list()])

    def test_list_empty_repo(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        mgr = FeatureBranchManager(gitflow)
        self.assertItemsEqual([], mgr.list())

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
        self.assertEquals('feature/even', mgr.by_name_prefix('e').name)
        self.assertEquals('feature/recursion', mgr.by_name_prefix('re').name)

    @copy_from_fixture('sample_repo')
    def test_by_nameprefix_not_unique_enough(self):
        gitflow = GitFlow()
        mgr = FeatureBranchManager(gitflow)
        mgr.create('rescue')
        self.assertRaises(PrefixNotUniqueError, mgr.by_name_prefix, 're')
        self.assertRaises(NoSuchBranchError, mgr.by_name_prefix, 'nonexisting')


    def test_create_new_feature_branch(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        gitflow.init()
        mgr = FeatureBranchManager(gitflow)
        self.assertEqual(0, len(mgr.list()))
        new_branch = mgr.create('foo')
        self.assertEqual(1, len(mgr.list()))
        self.assertEqual('feature/foo', mgr.list()[0].name)

    @copy_from_fixture('sample_repo')
    def test_create_new_feature_from_alt_base(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)

        new_branch = mgr.create('foo', 'feature/even')
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['feature/even'].commit)

    def test_feature_branch_origin(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        gitflow.init()
        mgr = FeatureBranchManager(gitflow)
        new_branch = mgr.create('foobar')
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['develop'].commit)

    def test_create_existing_feature_branch_yields_raises_error(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        gitflow.init()
        mgr = FeatureBranchManager(gitflow)
        mgr.create('foo')
        self.assertRaises(BranchExistsError, mgr.create, 'foo')

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
        fake_commit(self.repo, 'Dummy commit #1')
        fake_commit(self.repo, 'Dummy commit #2')
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


    @copy_from_fixture('sample_repo')
    def test_merge_feature_with_multiple_commits(self):
        gitflow = GitFlow(self.repo)
        mgr = FeatureBranchManager(gitflow)

        dc0 = gitflow.develop().commit
        mgr.merge('even', 'develop')
        dc1 = gitflow.develop().commit

        # Assert merge commit has been made
        self.assertEqual(2, len(dc1.parents))
        self.assertEqual(
                "Merge branch 'feature/even' into develop\n",
                dc1.message)

        # Assert develop branch advanced
        self.assertNotEqual(dc0, dc1)

    @copy_from_fixture('sample_repo')
    def test_merge_feature_with_single_commit(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()
        mgr = FeatureBranchManager(gitflow)

        dc0 = gitflow.develop().commit
        mgr.merge('recursion', 'develop')
        dc1 = gitflow.develop().commit

        # Assert no merge commit has been made
        self.assertEqual(1, len(dc1.parents))
        self.assertEqual('Made the definition of odd recursive.\n',
                dc1.message)

        # Assert develop branch advanced
        self.assertNotEqual(dc0, dc1)

    def test_merge_feature_without_commits(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        gitflow.init()
        mgr = FeatureBranchManager(gitflow)

        dc0 = gitflow.develop().commit
        mgr.create('newstuff')
        mgr.merge('newstuff', 'develop')
        dc1 = gitflow.develop().commit

        # Assert the develop tip is unchanged by the merge
        self.assertEqual(dc0, dc1)


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
        self.assertNotIn('feature/even',
                [b.name for b in self.repo.branches])

        # Merge commit message
        self.assertEquals('Finished feature even.\n', dc1.message)


class TestReleaseBranchManager(TestCase):
    def test_empty_repo_has_no_releases(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
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

    def test_create_new_release_branch(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
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

    def test_release_branch_origin(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        gitflow.init()
        mgr = ReleaseBranchManager(gitflow)
        new_branch = mgr.create('1.1')
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['develop'].commit)

    def test_create_existing_release_branch_yields_raises_error(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        gitflow.init()
        mgr = ReleaseBranchManager(gitflow)
        mgr.create('1.0')
        self.assertRaises(BranchExistsError, mgr.create, '1.0')

    def test_create_release_changes_active_branch(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        gitflow.init()
        mgr = ReleaseBranchManager(gitflow)

        self.assertEquals('master', repo.active_branch.name)
        mgr.create('1.0')
        self.assertEquals('release/1.0', repo.active_branch.name)

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

        # Finishing removes the release branch
        self.assertNotIn('release/1.0',
                [b.name for b in self.repo.branches])

        # Merge commit message
        self.assertEquals('Finished release 1.0.\n', dc1.message)


class TestHotfixBranchManager(TestCase):
    def test_create_new_hotfix_branch(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        gitflow.init()
        mgr = HotfixBranchManager(gitflow)
        self.assertEqual(0, len(mgr.list()))
        new_branch = mgr.create('1.2.3')
        self.assertEqual(1, len(mgr.list()))
        self.assertEqual('hotfix/1.2.3', mgr.list()[0].name)

    @copy_from_fixture('sample_repo')
    def test_hotfix_branch_origin(self):
        gitflow = GitFlow()
        mgr = HotfixBranchManager(gitflow)
        new_branch = mgr.create('3.14-beta5')
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['master'].commit)

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
        self.assertNotIn('hotfix/1.2.3',
                [b.name for b in self.repo.branches])

        # Merge commit message
        self.assertEquals('Finished hotfix 1.2.3.\n', dc1.message)


class TestSupportBranchManager(TestCase):
    def test_create_new_support_branch(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        gitflow.init()
        mgr = SupportBranchManager(gitflow)
        self.assertEqual(0, len(mgr.list()))
        new_branch = mgr.create('1.x')
        self.assertEqual(1, len(mgr.list()))
        self.assertEqual('support/1.x', mgr.list()[0].name)

    @copy_from_fixture('sample_repo')
    def test_support_branch_origin(self):
        gitflow = GitFlow()
        mgr = SupportBranchManager(gitflow)
        new_branch = mgr.create('legacy')
        self.assertEqual(new_branch.commit,
                gitflow.repo.branches['master'].commit)

    def test_support_branches_cannot_be_finished(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        gitflow.init()
        mgr = SupportBranchManager(gitflow)
        mgr.create('1.x')
        self.assertRaises(NotImplementedError, mgr.finish, '1.x')

