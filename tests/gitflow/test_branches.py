from unittest2 import TestCase, skip
from gitflow.core import GitFlow
from gitflow.branches import Branch
from tests.helpers import sandboxed_git_repo


class FooBranch(Branch):
    """
    A fictious Foo branch, used to test Branch functionality, but we need
    a concrete class, since Branch is an "abstract" class.
    """
    identifier = 'abc'
    prefix = 'xyz/'


class TestBranch(TestCase):
    def test_branch_init(self):
        fb = FooBranch('foo')
        self.assertEquals('foo', fb.shortname)
        self.assertEquals('xyz/foo', fb.name)

    def test_branch_init_with_alternate_prefix(self):
        fb = FooBranch('foo', 'xyz-')
        self.assertEquals('foo', fb.shortname)
        self.assertEquals('xyz-foo', fb.name)

    def test_branch_init_without_prefix(self):
        fb = FooBranch('foo', '')
        self.assertEquals('foo', fb.shortname)
        self.assertEquals('foo', fb.name)

    def test_branch_describes_itself(self):
        fb = FooBranch('foo')
        self.assertEquals('<tests.test_gitflow.test_branches.FooBranch "xyz/foo">', str(fb))



class FeatureBranch(TestCase):
    @skip
    @sandboxed_git_repo
    def test_feature_branch(self):
        gitflow = GitFlow()
        fb = FeatureBranch('foo')
        self.assertEquals('<gitflow.branches.FeatureBranch "feature/foo">',
                str(fb))

