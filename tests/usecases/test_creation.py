from unittest2 import TestCase, skip
from gitflow.core import GitFlow
from tests.helpers.factory import create_git_repo


class TestGitFlow(TestCase):

    @skip
    def test_create(self):
        create_git_repo(self)
        gitflow = GitFlow()

        self.assertEquals([], self.repo.branches)

        gitflow.init()

        self.assertEquals(['develop', 'master'],
                [b.name for b in self.repo.branches])

        fb = gitflow.create('feature', 'foo')


