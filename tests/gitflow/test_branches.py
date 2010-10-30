from unittest2 import TestCase, skip
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

