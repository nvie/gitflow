from unittest2 import TestCase, skip
from gitflow.core import GitFlow
from tests.helpers import sandboxed, sandboxed_git_repo, copy_from_fixture


class TestGitFlow(TestCase):

    @skip
    @sandboxed_git_repo
    def test_create(self):
        gitflow = GitFlow()
        repo = gitflow.repo

        self.assertEquals([], self.repo.branches)

        gitflow.init()

        self.assertEquals(['develop', 'master'],
                [b.name for b in self.repo.branches])

        fb = gitflow.create('feature', 'foo')


