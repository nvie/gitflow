from unittest2 import TestCase, skip
import os
import tempfile
from ConfigParser import NoOptionError, NoSectionError
from git import Repo
import shutil
from gitflow import GitFlow, NotInitialized, BranchExists, InvalidOperation, \
        DirtyWorkingTreeError


class TestGitFlow(TestCase):

    # Pick your fixture
    def new_sandbox(self):
        """
        This method sets up a temporary, self-destructing empty directory, to
        be used as a sandbox.  Files created/modified outside of the sandbox
        aren't cleaned up by this method.
        """
        ram_disk = '/Volumes/RAM_Disk'
        dir = None
        if os.path.exists(ram_disk):
            dir = ram_disk
        tmp = tempfile.mkdtemp(dir=dir)
        self.addCleanup(shutil.rmtree, tmp)
        return tmp

    def fresh_git_repo(self):
        """
        This method sets up a temporary, self-destructing empty sandbox.  There
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


    # Sanity checking
    def test_new_repo_is_not_dirty(self):
        repo = self.new_sandbox()
        gitflow = GitFlow(repo)
        gitflow.init()
        self.assertFalse(gitflow.is_dirty())

    def test_existing_repo_is_not_dirty(self):
        repo = self.git_repo_copy_from_fixture('dirty_sample_repo')
        gitflow = GitFlow(repo)
        self.assertTrue(gitflow.is_dirty())


    def test_gitflow_cannot_get_status_on_empty_sandbox(self):
        repo = self.new_sandbox()
        gitflow = GitFlow(repo)
        self.assertRaises(NotInitialized, gitflow.status)

    def test_gitflow_status_on_fresh_repo(self):
        repo = self.fresh_git_repo()
        gitflow = GitFlow(repo)
        self.assertEquals([], gitflow.status())

    def test_gitflow_status_on_sample_repo(self):
        repo = self.git_repo_copy_from_fixture('sample_repo')
        gitflow = GitFlow(repo)
        self.assertItemsEqual([
                ('master', '296586bb164c946cad10d37e82570f60e6348df9', False),
                ('develop', '2b34cd2e1617e5f0d4e077c6ec092b9f50ed49a3', False),
                ('feature/recursion', '54d59c872469c7bf34d540d2fb3128a97502b73f', True),
                ('feature/even', 'e56be18dada9e81ca7969760ddea357b0c4c9412', False),
            ], gitflow.status())


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
    def test_gitflow_empty_repo_has_no_features(self):
        repo = self.fresh_git_repo()
        gitflow = GitFlow(repo)
        gitflow.init()
        self.assertItemsEqual([], gitflow.feature_branches())

    def test_gitflow_sample_repo_has_features(self):
        repo = self.git_repo_copy_from_fixture('sample_repo')
        gitflow = GitFlow(repo)
        self.assertItemsEqual(['feature/even', 'feature/recursion'],
                gitflow.feature_branches())

    def test_gitflow_create_feature_branch(self):
        repo = self.fresh_git_repo()
        gitflow = GitFlow(repo)
        gitflow.init()
        gitflow.new_feature_branch('foo')
        branches = gitflow.feature_branches()
        self.assertIn('feature/foo', branches)

    def test_gitflow_cannot_create_existing_feature(self):
        repo = self.fresh_git_repo()
        gitflow = GitFlow(repo)
        gitflow.init()
        gitflow.new_feature_branch('foo')
        self.assertRaises(BranchExists, gitflow.new_feature_branch, 'foo')

    def test_gitflow_create_feature_from_alt_base(self):
        repo = self.git_repo_copy_from_fixture('sample_repo')
        gitflow = GitFlow(repo)
        gitflow.init()

        new_branch = gitflow.new_feature_branch('foo', 'feature/even')
        branches = gitflow.feature_branches()
        self.assertIn('feature/even', branches)
        self.assertIn('feature/foo', branches)
        self.assertEquals(repo.commit('feature/even'), new_branch.commit)

    def test_gitflow_create_feature_changes_active_branch(self):
        repo = self.git_repo_copy_from_fixture('sample_repo')
        gitflow = GitFlow(repo)

        self.assertEquals('feature/recursion', repo.active_branch.name)
        gitflow.new_feature_branch('foo')
        self.assertEquals('feature/foo', repo.active_branch.name)

    def test_gitflow_cannot_create_feature_if_this_leads_to_data_loss(self):
        repo = self.git_repo_copy_from_fixture('dirty_sample_repo')
        gitflow = GitFlow(repo)
        self.assertRaisesRegexp(DirtyWorkingTreeError,
                "Cannot merge. Entry .* would be overwritten",
                gitflow.new_feature_branch, 'foo')

    def test_gitflow_delete_feature(self):
        repo = self.git_repo_copy_from_fixture('sample_repo')
        gitflow = GitFlow(repo)

        self.assertIn('feature/even', gitflow.feature_branches())
        gitflow.delete_feature_branch('even')
        self.assertNotIn('feature/even', gitflow.feature_branches())

    def test_gitflow_cannot_delete_current_feature(self):
        repo = self.git_repo_copy_from_fixture('sample_repo')
        gitflow = GitFlow(repo)
        self.assertRaisesRegexp(InvalidOperation, 'Cannot delete the branch .* '
                'which you are currently on',
                gitflow.delete_feature_branch, 'recursion')

    def test_gitflow_cannot_delete_non_existing_feature(self):
        repo = self.git_repo_copy_from_fixture('sample_repo')
        gitflow = GitFlow(repo)
        self.assertRaisesRegexp(InvalidOperation, 'Branch .* not found',
                gitflow.delete_feature_branch, 'nonexisting')


    """
    Use case:

    $ git flow init
    $ git flow feature start foo
    $ git flow status
      develop: 4826bdf
      master: 4826bdf
    * feature/foo: 7c8928a
    $ git commit -m 'foo'
    $ git commit -m 'bar'
    $ git flow feature start bar
    $ git commit -m 'qux'
    $ git flow feature finish foo
    $ git flow undo        # new!
    $ git flow feature finish bar
    There were merge conflicts, resolve them now!
    $ git flow abort       # new!

    """

