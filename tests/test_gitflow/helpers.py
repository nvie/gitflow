import os
import shutil
import tempfile
from functools import wraps
from unittest2 import TestCase
from git import Repo


# Pick your fixture
def sandboxed(f):
    """
    This decorator sets up a temporary, self-destructing empty directory, to be
    used as a sandbox.  The name of the directory is stored in self.sandbox
    attribute.  Files created/modified outside of the sandbox aren't cleaned up
    by this method.
    """
    @wraps(f)
    def _inner(self, *args, **kwargs):
        assert isinstance(self, TestCase)
        ram_disk = '/Volumes/RAM_Disk'
        dir = None
        if os.path.exists(ram_disk):
            dir = ram_disk
        self.sandbox = tempfile.mkdtemp(dir=dir)
        self.addCleanup(shutil.rmtree, self.sandbox)

        # Call the function
        f(self, *args, **kwargs)
    return _inner


def sandboxed_git_repo(f):
    @wraps(f)
    @sandboxed
    def _inner(self, *args, **kwargs):
        """
        This method sets up a temporary, self-destructing empty sandbox.  There
        hasn't been any git flow initialization yet.
        """
        self.repo = Repo.init(self.sandbox)
        f(self, *args, **kwargs)
    return _inner


def git_repo_copy_from_fixture(self, fixture_name):
    """
    This method sets up a temporary, self-destructing sandbox and copies
    a given fixture recursively into it.  This is useful for fixtures that
    represent changes in the configuration or dirty working directories.
    """
    src = 'tests/fixtures/%s' % fixture_name
    dest = os.path.join(self.new_sandbox(), fixture_name)
    shutil.copytree(src, dest)
    shutil.move(os.path.join(dest, 'dot_git'), os.path.join(dest, '.git'))
    cpy = Repo(dest)
    return cpy


def git_repo_clone_from_fixture(self, fixture_name):
    """
    This method sets up a temporary, self-destructing sandbox, cloned from
    a given fixture.  In contrast to a filesystem copy, a clone always has
    fresh configuration and a clean working directory.
    """
    tmp = self.new_sandbox()
    fixture_repo = 'tests/fixtures/%s/dot_git' % fixture_name
    clone = Repo(fixture_repo).clone(tmp)
    return clone


