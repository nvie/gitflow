from unittest2 import TestCase, skip
from testlib import fresh_repo
from gitflow.core import GitFlow
from gitflow.branches import Branch, FeatureBranch


class TestFeatureBranch(TestCase):
    def test_feature_branch_init(self):
        gitflow = GitFlow()
        fb = FeatureBranch(gitflow, 'foo')
        self.assertEquals('foo', fb.name)
        self.assertEquals('feature/foo', fb.fullname)

    @skip
    def test_feature_branch_init_with_alternate_prefix(self):
        gitflow = self.
        #gitflow.init(feature='fb-')
        fb = FeatureBranch(gitflow, 'foo')
        self.assertEquals('foo', fb.name)
        self.assertEquals('feature/foo', fb.fullname)
