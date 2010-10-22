from unittest2 import TestCase, skip
import os
import tempfile
from ConfigParser import NoOptionError, NoSectionError
from git import Repo
import shutil
from gitflow import GitFlow


class TestGitFlow(TestCase):

    #
    # Sandboxing helpers
    #
    def new_sandbox(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        return tmp

    def empty_repo(self):
        """
        This method sets up an temporary, self-destructing empty sandbox.  There
        hasn't been any git flow initialization yet.
        """
        tmp = self.new_sandbox()
        repo = Repo.init(tmp)
        return repo

    def copy_from_fixture(self, fixture_name):
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

    def clone_from_fixture(self, fixture_name):
        """
        This method sets up a temporary, self-destructing sandbox, cloned from
        a given fixture.  In contrast to a filesystem copy, a clone always has
        fresh configuration and a clean working directory.
        """
        tmp = self.new_sandbox()
        fixture_repo = 'tests/fixtures/%s/dot_git' % fixture_name
        clone = Repo(fixture_repo).clone(tmp)
        return clone


    # Configuration
    def test_default_branchnames(self):
        repo = self.empty_repo()
        cfg = GitFlow(repo)
        self.assertEquals('master', cfg.master())
        self.assertEquals('develop', cfg.develop())
        self.assertEquals('hotfix/', cfg.hotfix_prefix())
        self.assertEquals('release/', cfg.release_prefix())
        self.assertEquals('support/', cfg.support_prefix())

    def test_config_reader(self):
        repo = self.copy_from_fixture('custom_repo')
        gitflow = GitFlow(repo)
        self.assertRaises(NoSectionError, gitflow.get,
                'nonexisting.nonexisting')
        self.assertRaises(NoSectionError, gitflow.get,
                'section.subsection.propname')
        self.assertRaises(NoOptionError, gitflow.get, 'foo.nonexisting')
        self.assertEquals('qux', gitflow.get('foo.bar'))

    def test_custom_branchnames(self):
        cfg = GitFlow(Repo('tests/fixtures/custom_repo/dot_git'))
        self.assertEquals('production', cfg.master())
        self.assertEquals('master', cfg.develop())
        self.assertEquals('hf-', cfg.hotfix_prefix())
        self.assertEquals('rel-', cfg.release_prefix())
        self.assertEquals('supp-', cfg.support_prefix())


    # git flow init
    def test_gitflow_init_marks_initialized(self):
        repo = self.empty_repo()
        gitflow = GitFlow(repo)
        self.assertFalse(gitflow.initialized)
        gitflow.init()
        self.assertTrue(gitflow.initialized)

    def test_gitflow_init_initializes(self):
        repo = self.empty_repo()
        gitflow = GitFlow(repo)
        self.assertRaises(NoSectionError,
                gitflow.repo.config_reader().get, 'gitflow "branch"', 'master')
        self.assertRaises(NoSectionError,
                gitflow.repo.config_reader().get, 'gitflow "branch"', 'develop')
        gitflow.init()
        self.assertEquals('master',
                gitflow.repo.config_reader().get('gitflow "branch"', 'master'))
        self.assertEquals('develop',
                gitflow.repo.config_reader().get('gitflow "branch"', 'develop'))
