#
# This file is part of `gitflow`.
# Copyright (c) 2010-2011 Vincent Driessen
# Copyright (c) 2012 Hartmut Goebel
# Distributed under a BSD-like license. For full terms see the file LICENSE.txt
#

import os
import shutil
import tempfile
from functools import wraps

from unittest2 import TestCase
from git import Repo

__copyright__ = "2010-2011 Vincent Driessen; 2012 Hartmut Goebel"
__license__ = "BSD"

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


def set_gnupg_home(func):
    """
    Decorator which changes the current working dir to the one of the
    git repository in order to assure relative paths are handled
    correctly.
    """
    @wraps(func)
    def _inner(*args, **kwargs):
        root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        gpghome = os.path.join(root, 'fixtures', 'gnupg')
        oldval = os.environ.get('GNUPGHOME')
        os.environ['GNUPGHOME'] = gpghome
        func(*args, **kwargs)
        if oldval is not None:
            os.environ['GNUPGHOME'] = oldval
        else:
            del os.environ['GNUPGHOME']
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

def remote_clone_from_fixture(fixture_name, copy_config=True):
    """
    This decorator sets up a temporary, self-destructing sandbox,
    cloned from a sandboxed copy of the fixture.  In contrast to a
    filesystem copy, the clone always has a clean working directory.

    :param copy_config:
         Copy the `gitflow` parts of the original repo into the clone.

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
            self.repo = self.remote.clone(clone, origin='my-remote')
            if copy_config:
                copy_gitflow_config(self.remote, self.repo)
            self.repo.config_writer(config_level='repository').set_value(
                'gitflow', 'origin', 'my-remote')
            os.chdir(clone)
            f(self, *args, **kwargs)
        return _inner
    return _outer


def git_working_dir(func):
    """
    Decorator which changes the current working dir to the one of the
    git repository in order to assure relative paths are handled
    correctly.
    """
    # Adopted from GitPython's git.index.util.git_working_dir
    # Copyright (C) 2008, 2009 Michael Trier (mtrier@gmail.com) and
    #    contributors
    # Released under the BSD License:
    # http://www.opensource.org/licenses/bsd-license.php
    @wraps(func)
    def set_git_working_dir(repo, *args, **kwargs):
        cur_wd = os.getcwd()
        os.chdir(repo.working_tree_dir)
        try:
            return func(repo, *args, **kwargs)
        finally:
            os.chdir(cur_wd)

    return set_git_working_dir


@git_working_dir
def fake_commit(repo, message, append=True):
    if append:
        f = open('newfile.py', 'a')
    else:
        f = open('newfile.py', 'w')
    try:
        f.write('This is a dummy change.\n')
    finally:
        f.close()
    repo.index.add(['newfile.py'])
    return repo.index.commit(message)


def all_commits(repo, heads=None):
    s = set([])
    if heads:
        heads = [h for h in repo.heads if h.name in heads]
    else:
        heads = repo.heads
    for h in heads:
        s |= set(repo.iter_commits(h))
    return s
