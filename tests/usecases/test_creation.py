#
# This file is part of `gitflow`.
# Copyright (c) 2010-2011 Vincent Driessen
# Copyright (c) 2012 Hartmut Goebel
# Distributed under a BSD-like license. For full terms see the file LICENSE.txt
#

from unittest2 import TestCase, skip

from gitflow.core import GitFlow
from tests.helpers.factory import create_git_repo

__copyright__ = "2010-2011 Vincent Driessen; 2012 Hartmut Goebel"
__license__ = "BSD"


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


