from unittest2 import TestCase, skip
import os
import tempfile
from ConfigParser import NoOptionError, NoSectionError
from git import Repo
import shutil
from gitflow import GitFlow, NotInitialized


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
        repo = self.copy_from_fixture('custom_repo')
        gitflow = GitFlow(repo)
        self.assertEquals('production', gitflow.master())
        self.assertEquals('master', gitflow.develop())
        self.assertEquals('f-', gitflow.feature_prefix())
        self.assertEquals('hf-', gitflow.hotfix_prefix())
        self.assertEquals('rel-', gitflow.release_prefix())
        self.assertEquals('supp-', gitflow.support_prefix())


    # git flow init
    def test_gitflow_init_marks_initialized(self):
        repo = self.empty_repo()
        gitflow = GitFlow(repo)
        self.assertFalse(gitflow.is_initialized())
        gitflow.init()
        self.assertTrue(gitflow.is_initialized())

    def test_gitflow_throws_errors_before_init(self):
        repo = self.empty_repo()
        gitflow = GitFlow(repo)
        self.assertRaises(NotInitialized, gitflow.master)
        self.assertRaises(NotInitialized, gitflow.develop)
        self.assertRaises(NotInitialized, gitflow.feature_prefix)
        self.assertRaises(NotInitialized, gitflow.hotfix_prefix)
        self.assertRaises(NotInitialized, gitflow.release_prefix)
        self.assertRaises(NotInitialized, gitflow.support_prefix)

    def test_gitflow_init_initializes_default_config(self):
        repo = self.empty_repo()
        gitflow = GitFlow(repo)
        gitflow.init()
        self.assertEquals('master', gitflow.master())
        self.assertEquals('develop', gitflow.develop())
        self.assertEquals('feature/', gitflow.feature_prefix())
        self.assertEquals('hotfix/', gitflow.hotfix_prefix())
        self.assertEquals('release/', gitflow.release_prefix())
        self.assertEquals('support/', gitflow.support_prefix())

    def test_gitflow_init_with_alternative_config(self):
        repo = self.empty_repo()
        gitflow = GitFlow(repo)
        gitflow.init(master='foo', develop='bar', feature='f-', hotfix='hf-',
                release='rel-', support='supp-')
        self.assertEquals('foo', gitflow.master())
        self.assertEquals('bar', gitflow.develop())
        self.assertEquals('f-', gitflow.feature_prefix())
        self.assertEquals('hf-', gitflow.hotfix_prefix())
        self.assertEquals('rel-', gitflow.release_prefix())
        self.assertEquals('supp-', gitflow.support_prefix())

