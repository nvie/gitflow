#
# This file is part of `gitflow`.
# Copyright (c) 2010-2011 Vincent Driessen
# Copyright (c) 2012 Hartmut Goebel
# Distributed under a BSD-like license. For full terms see the file LICENSE.txt
#

import os
import shutil
import tempfile

from unittest2 import TestCase
from git import Repo

__copyright__ = "2010-2011 Vincent Driessen; 2012 Hartmut Goebel"
__license__ = "BSD"

def create_sandbox(testcase):
    """
    Sets up a temporary, self-destructing directory and chdir to it.
    """
    assert isinstance(testcase, TestCase)

    dir = None
    ram_disk = '/Volumes/RAM_Disk'
    if os.path.exists(ram_disk):
        dir = ram_disk
    sandbox = tempfile.mkdtemp(dir=dir)
    testcase.addCleanup(shutil.rmtree, sandbox)

    os.chdir(sandbox)

    return sandbox


def create_git_repo(testcase):
    """
    Sets up a temporary, self-destructing empty Git repository using "git init".
    There hasn't been any git flow initialization yet.
    """
    create_sandbox(testcase)
    repo = Repo.init()
    return repo

