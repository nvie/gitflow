from unittest2 import TestCase, skip
from git import GitCommandError
from gitflow.core import GitFlow
from gitflow.branches import BranchManager, FeatureBranchManager
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
    @sandboxed_git_repo
    def test_empty_repo_has_no_features(self):
        gitflow = GitFlow()
        mgr = FeatureBranchManager(gitflow)
        self.assertItemsEqual([], mgr.list())

    @copy_from_fixture('sample_repo')
    def test_list(self):
        gitflow = GitFlow()
        mgr = FeatureBranchManager(gitflow)
        expected = ['feature/even', 'feature/recursion']
        self.assertItemsEqual(expected, [b.name for b in mgr.list()])

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
        mgr.create('foo')
        self.assertEqual(1, len(mgr.list()))
        self.assertEqual('feature/foo', mgr.list()[0].name)

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
        self.assertRaisesRegexp(GitCommandError,
                "Your local changes to the following files would be overwritten",
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

