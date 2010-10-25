from unittest2 import TestCase, skip
import os
import tempfile
from ConfigParser import NoOptionError, NoSectionError
from git import Repo
import shutil
from gitflow import GitFlow, NotInitialized, BranchExists


class TestGitFlow(TestCase):

    # Pick your fixture
    def new_sandbox(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        return tmp

    def fresh_git_repo(self):
        """
        This method sets up an temporary, self-destructing empty sandbox.  There
        hasn't been any git flow initialization yet.
        """
        tmp = self.new_sandbox()
        repo = Repo.init(tmp)
        return repo

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


    # Helper methods
    def all_commits(self, repo):
        s = set([])
        for h in repo.heads:
            s |= set(repo.iter_commits(h))
        return s


    # Configuration
    def test_config_reader(self):
        repo = self.git_repo_copy_from_fixture('custom_repo')
        gitflow = GitFlow(repo)
        gitflow.init()
        self.assertRaises(ValueError, gitflow.get,
                'invalid_setting_since_this_has_no_dot')
        self.assertRaises(NoSectionError, gitflow.get,
                'nonexisting.nonexisting')
        self.assertRaises(NoSectionError, gitflow.get,
                'section.subsection.propname')
        self.assertRaises(NoOptionError, gitflow.get, 'foo.nonexisting')
        self.assertEquals('qux', gitflow.get('foo.bar'))

    def test_custom_branchnames(self):
        repo = self.git_repo_copy_from_fixture('custom_repo')
        gitflow = GitFlow(repo)
        gitflow.init()
        self.assertEquals('production', gitflow.master_name())
        self.assertEquals('master', gitflow.develop_name())
        self.assertEquals('f-', gitflow.feature_prefix())
        self.assertEquals('hf-', gitflow.hotfix_prefix())
        self.assertEquals('rel-', gitflow.release_prefix())
        self.assertEquals('supp-', gitflow.support_prefix())


    # Initialization
    def test_branch_names_fails_in_new_sandbox(self):
        repo = self.new_sandbox()
        gitflow = GitFlow(repo)
        self.assertRaises(NotInitialized, gitflow.branch_names)

    def test_empty_repo_has_no_branches(self):
        repo = self.fresh_git_repo()
        gitflow = GitFlow(repo)
        self.assertItemsEqual([], gitflow.branch_names())

    def test_custom_repo_has_branches(self):
        repo = self.git_repo_copy_from_fixture('custom_repo')
        gitflow = GitFlow(repo)
        gitflow.init()
        self.assertItemsEqual(['master', 'production'],
                gitflow.branch_names())


    # git flow init
    def test_gitflow_init_inits_underlying_git_repo(self):
        empty_dir = self.new_sandbox()
        gitflow = GitFlow(empty_dir)
        dot_git_dir = os.path.join(empty_dir, '.git')
        self.assertFalse(os.path.exists(dot_git_dir))
        gitflow.init()
        self.assertTrue(os.path.exists(dot_git_dir))
        self.assertTrue(gitflow.is_initialized())

    def test_gitflow_init_marks_initialized(self):
        repo = self.fresh_git_repo()
        gitflow = GitFlow(repo)
        self.assertFalse(gitflow.is_initialized())
        gitflow.init()
        self.assertTrue(gitflow.is_initialized())

    def test_gitflow_throws_errors_before_init(self):
        repo = self.fresh_git_repo()
        gitflow = GitFlow(repo)
        self.assertRaises(NotInitialized, gitflow.master_name)
        self.assertRaises(NotInitialized, gitflow.develop_name)
        self.assertRaises(NotInitialized, gitflow.feature_prefix)
        self.assertRaises(NotInitialized, gitflow.hotfix_prefix)
        self.assertRaises(NotInitialized, gitflow.release_prefix)
        self.assertRaises(NotInitialized, gitflow.support_prefix)

    def test_gitflow_init_initializes_default_config(self):
        repo = self.fresh_git_repo()
        gitflow = GitFlow(repo)
        gitflow.init()
        self.assertEquals('master', gitflow.master_name())
        self.assertEquals('develop', gitflow.develop_name())
        self.assertEquals('feature/', gitflow.feature_prefix())
        self.assertEquals('hotfix/', gitflow.hotfix_prefix())
        self.assertEquals('release/', gitflow.release_prefix())
        self.assertEquals('support/', gitflow.support_prefix())

    def test_gitflow_init_with_alternative_config(self):
        repo = self.fresh_git_repo()
        gitflow = GitFlow(repo)
        gitflow.init(master='foo', develop='bar', feature='f-', hotfix='hf-',
                release='rel-', support='supp-')
        self.assertEquals('foo', gitflow.master_name())
        self.assertEquals('bar', gitflow.develop_name())
        self.assertEquals('f-', gitflow.feature_prefix())
        self.assertEquals('hf-', gitflow.hotfix_prefix())
        self.assertEquals('rel-', gitflow.release_prefix())
        self.assertEquals('supp-', gitflow.support_prefix())

    def test_gitflow_init_config_with_partly_inited(self):
        repo = self.git_repo_copy_from_fixture('partly_inited')
        gitflow = GitFlow(repo)
        gitflow.init()

        # Already set in fixture, shouldn't change
        self.assertEquals('production', gitflow.master_name())
        self.assertEquals('f-', gitflow.feature_prefix())

        # Implicit defaults
        self.assertEquals('develop', gitflow.develop_name())
        self.assertEquals('hotfix/', gitflow.hotfix_prefix())
        self.assertEquals('release/', gitflow.release_prefix())
        self.assertEquals('support/', gitflow.support_prefix())

    def test_gitflow_init_creates_no_extra_commits(self):
        repo = self.git_repo_copy_from_fixture('sample_repo')
        all_commits_before_init = self.all_commits(repo)
        gitflow = GitFlow(repo)
        gitflow.init()
        all_commits_after_init = self.all_commits(repo)
        self.assertEquals(all_commits_before_init, all_commits_after_init)

    def test_gitflow_init_creates_no_extra_branches(self):
        repo = self.git_repo_copy_from_fixture('sample_repo')
        heads_before_init = [h.name for h in repo.heads]
        gitflow = GitFlow(repo)
        gitflow.init()
        heads_after_init = [h.name for h in repo.heads]
        self.assertItemsEqual(heads_before_init, heads_after_init)

    def test_gitflow_init_creates_initial_commit(self):
        repo = self.fresh_git_repo()
        all_commits_before_init = self.all_commits(repo)
        gitflow = GitFlow(repo)
        gitflow.init()
        all_commits_after_init = self.all_commits(repo)
        self.assertNotEquals(all_commits_before_init, all_commits_after_init)
        self.assertEquals('Initial commit', repo.heads.master.commit.message)

    def test_gitflow_init_creates_branches(self):
        repo = self.fresh_git_repo()
        gitflow = GitFlow(repo)
        gitflow.init()
        self.assertItemsEqual(['master', 'develop'],
                gitflow.branch_names())

    def test_gitflow_force_reinit_partly_inited(self):
        repo = self.git_repo_copy_from_fixture('partly_inited')
        gitflow = GitFlow(repo)
        gitflow.init(force_defaults=True)

        # Implicit defaults
        self.assertEquals('develop', gitflow.develop_name())
        self.assertEquals('hotfix/', gitflow.hotfix_prefix())
        self.assertEquals('release/', gitflow.release_prefix())
        self.assertEquals('support/', gitflow.support_prefix())

        # Explicitly forced back to defaults
        self.assertEquals('master', gitflow.master_name())
        self.assertEquals('feature/', gitflow.feature_prefix())


    # git flow feature
    def test_gitflow_empty_repo_has_no_feature_branches(self):
        repo = self.fresh_git_repo()
        gitflow = GitFlow(repo)
        gitflow.init()
        self.assertItemsEqual([], gitflow.feature_branches())

    def test_gitflow_sample_repo_has_feature_branches(self):
        repo = self.git_repo_copy_from_fixture('sample_repo')
        gitflow = GitFlow(repo)
        gitflow.init()
        self.assertItemsEqual(['feature/even', 'feature/recursion'], gitflow.feature_branches())

    def test_gitflow_create_feature_branch(self):
        repo = self.fresh_git_repo()
        gitflow = GitFlow(repo)
        gitflow.init()
        gitflow.new_feature_branch('foo')
        branches = gitflow.feature_branches()
        self.assertIn('feature/foo', branches)

    def test_gitflow_cant_create_existing_feature_branch(self):
        repo = self.fresh_git_repo()
        gitflow = GitFlow(repo)
        gitflow.init()
        gitflow.new_feature_branch('foo')
        self.assertRaises(BranchExists, gitflow.new_feature_branch, 'foo')

    def test_gitflow_create_feature_from_alt_base(self):
        repo = self.git_repo_copy_from_fixture('sample_repo')
        gitflow = GitFlow(repo)
        gitflow.init()

        existing_tip = repo.commit('feature/even')
        new_branch = gitflow.new_feature_branch('foo', 'feature/even')
        branches = gitflow.feature_branches()
        self.assertIn('feature/even', branches)
        self.assertIn('feature/foo', branches)
        self.assertEquals(repo.commit('feature/even'), new_branch.commit)

