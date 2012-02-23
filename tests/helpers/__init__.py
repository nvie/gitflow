import os
import shutil
import tempfile
from functools import wraps
from unittest2 import TestCase
from git import Repo


def sandboxed(f):
    """
    This decorator sets up a temporary, self-destructing empty directory and
    switches the current directory to it.  The name of the directory is stored
    in self.sandbox attribute.  Files created/modified outside of the sandbox
    aren't cleaned up by this method.
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

        os.chdir(self.sandbox)

        # Call the function
        f(self, *args, **kwargs)
    return _inner

def copy_from_fixture(fixture_name):
    """
    This decorator sets up a temporary, self-destructing sandbox and copies
    a given fixture into it.  The repo is accessible inside the function via the
    self.repo attribute.  This is useful for fixtures that represent changes in
    the configuration or dirty working directories.
    """
    def _outer(f):
        @wraps(f)
        @sandboxed
        def _inner(self, *args, **kwargs):
            root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            src = os.path.join(root, 'fixtures', fixture_name)
            dest = os.path.join(self.sandbox, fixture_name)
            shutil.copytree(src, dest)
            os.chdir(dest)
            shutil.move('dot_git', '.git')
            self.repo = Repo(dest)
            f(self, *args, **kwargs)
        return _inner
    return _outer

def clone_from_fixture(fixture_name):
    """
    This decorator sets up a temporary, self-destructing sandbox, cloned from
    a given fixture.  In contrast to a filesystem copy, a clone always has fresh
    configuration and a clean working directory.

    The repo is accesible via the self.repo attribute inside the tests.
    """
    def _outer(f):
        @wraps(f)
        @sandboxed
        def _inner(self, *args, **kwargs):
            root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            git_dir = os.path.join(root, 'fixtures', fixture_name, 'dot_git')
            self.repo = Repo(git_dir).clone(self.sandbox)
            f(self, *args, **kwargs)
        return _inner
    return _outer


def copy_gitflow_config(src, dest):
    reader = src.config_reader(config_level='repository')
    writer = dest.config_writer(config_level='repository')
    for section in reader.sections():
        if section.startswith('gitflow '):
            for item, value in reader.items(section):
                writer.set_value(section, item, value)
    del writer

def remote_clone_from_fixture(fixture_name):
    """
    This decorator sets up a temporary, self-destructing sandbox,
    cloned from a sandboxed copy of the fixture.  In contrast to a
    filesystem copy, the clone always has a clean working directory.

    The repo is accesible via the self.repo attribute inside the
    tests, the remote (clond) repo via `self.remote`.
    """
    def _outer(f):
        @wraps(f)
        @sandboxed
        def _inner(self, *args, **kwargs):
            root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            src = os.path.join(root, 'fixtures', fixture_name)
            dest = os.path.join(self.sandbox, 'remote')
            shutil.copytree(src, dest)
            os.chdir(dest)
            shutil.move('dot_git', '.git')
            self.remote = Repo(dest)
            clone = os.path.join(self.sandbox, 'clone')
            self.repo = self.remote.clone(clone)
            copy_gitflow_config(self.remote, self.repo)
            os.chdir(clone)
            f(self, *args, **kwargs)
        return _inner
    return _outer

