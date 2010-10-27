from unittest2 import TestCase, skip
from gitflow.core import GitFlow
from gitflow.branches import Branch, FeatureBranch
from helpers import sandboxed_git_repo


class TestFeatureBranch(TestCase):
    def test_feature_branch_init(self):
        fb = FeatureBranch('foo')
        self.assertEquals('foo', fb.name)
        self.assertEquals('feature/foo', fb.fullname)

    def test_feature_branch_init_with_alternate_prefix(self):
        fb = FeatureBranch('foo', 'fb-')
        self.assertEquals('foo', fb.name)
        self.assertEquals('fb-foo', fb.fullname)

    def test_feature_branch_init_without_prefix(self):
        fb = FeatureBranch('foo', '')
        self.assertEquals('foo', fb.name)
        self.assertEquals('foo', fb.fullname)
