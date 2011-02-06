import os
import shutil
import tempfile
from unittest2 import TestCase
from git import Repo


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

