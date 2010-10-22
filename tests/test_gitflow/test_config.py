from unittest2 import TestCase, skip
import os
import tempfile
from ConfigParser import NoOptionError, NoSectionError
from git import Repo
import shutil
import gitflow.config as mod


class TestBranchNaming(TestCase):

    #
    # Sandboxing helpers
    #
    def new_sandbox(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        return tmp

    def empty_repo(self):
        tmp = self.new_sandbox()
        repo = Repo.init(tmp)
        return repo

    def copy_from_fixture(self, fixture_name):
        src = 'tests/fixtures/%s' % fixture_name
        dest = os.path.join(self.new_sandbox(), fixture_name)
        shutil.copytree(src, dest)
        shutil.move(os.path.join(dest, 'dot_git'), os.path.join(dest, '.git'))
        cpy = Repo(dest)
        return cpy

    def clone_from_fixture(self, fixture_name):
        tmp = self.new_sandbox()
        fixture_repo = 'tests/fixtures/%s/dot_git' % fixture_name
        clone = Repo(fixture_repo).clone(tmp)
        return clone


    def test_default_branchnames(self):
        repo = self.empty_repo()
        cfg = mod.Config(repo.git_dir)
        self.assertEquals('master', cfg.master())
        self.assertEquals('develop', cfg.develop())
        self.assertEquals('hotfix/', cfg.hotfix_prefix())
        self.assertEquals('release/', cfg.release_prefix())
        self.assertEquals('support/', cfg.support_prefix())

    def test_config_reader(self):
        repo = self.copy_from_fixture('custom_repo')
        cfg = mod.Config(repo.git_dir)
        self.assertRaises(NoSectionError, cfg.get, 'nonexisting.nonexisting')
        self.assertRaises(NoSectionError, cfg.get, 'section.subsection.propname')
        self.assertRaises(NoOptionError, cfg.get, 'foo.nonexisting')
        self.assertEquals('qux', cfg.get('foo.bar'))

    def test_custom_branchnames(self):
        cfg = mod.Config('tests/fixtures/custom_repo/dot_git')
        self.assertEquals('production', cfg.master())
        self.assertEquals('master', cfg.develop())
        self.assertEquals('hf-', cfg.hotfix_prefix())
        self.assertEquals('rel-', cfg.release_prefix())
        self.assertEquals('supp-', cfg.support_prefix())

