from unittest2 import TestCase, skip
import os
import tempfile
from ConfigParser import NoOptionError, NoSectionError
from git import Repo, GitCommandError
import shutil
from gitflow.core import GitFlow, NotInitialized, BranchExists, InvalidOperation
from gitflow.branches import Branch
from tests.helpers import sandboxed, sandboxed_git_repo, copy_from_fixture


class TestGitFlow(TestCase):

    # Helper methods
    def all_commits(self, repo):
        s = set([])
        for h in repo.heads:
            s |= set(repo.iter_commits(h))
        return s


    # Configuration
    @copy_from_fixture('custom_repo')
    def test_config_reader(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()
        self.assertRaises(ValueError, gitflow.get,
                'invalid_setting_since_this_has_no_dot')
        self.assertRaises(NoSectionError, gitflow.get,
                'nonexisting.nonexisting')
        self.assertRaises(NoSectionError, gitflow.get,
                'section.subsection.propname')
        self.assertRaises(NoOptionError, gitflow.get, 'foo.nonexisting')
        self.assertEquals('qux', gitflow.get('foo.bar'))

    @copy_from_fixture('custom_repo')
    def test_custom_branchnames(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()
        self.assertEquals('production', gitflow.master_name())
        self.assertEquals('master', gitflow.develop_name())
        self.assertEquals('f-', gitflow.feature_prefix())
        self.assertEquals('hf-', gitflow.hotfix_prefix())
        self.assertEquals('rel-', gitflow.release_prefix())
        self.assertEquals('supp-', gitflow.support_prefix())


    # Initialization
    @sandboxed
    def test_branch_names_fails_in_new_sandbox(self):
        gitflow = GitFlow(self.sandbox)
        self.assertRaises(NotInitialized, gitflow.branch_names)

    @sandboxed_git_repo
    def test_empty_repo_has_no_branches(self):
        gitflow = GitFlow(self.repo)
        self.assertItemsEqual([], gitflow.branch_names())

    @copy_from_fixture('custom_repo')
    def test_custom_repo_has_branches(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()
        self.assertItemsEqual(['master', 'production'],
                gitflow.branch_names())


    # Sanity checking
    @sandboxed
    def test_new_repo_is_not_dirty(self):
        gitflow = GitFlow(self.sandbox)
        gitflow.init()
        self.assertFalse(gitflow.is_dirty())

    @copy_from_fixture('dirty_sample_repo')
    def test_existing_repo_is_not_dirty(self):
        gitflow = GitFlow(self.repo)
        self.assertTrue(gitflow.is_dirty())


    @sandboxed
    def test_gitflow_cannot_get_status_on_empty_sandbox(self):
        gitflow = GitFlow(self.sandbox)
        self.assertRaises(NotInitialized, gitflow.status)

    @sandboxed_git_repo
    def test_gitflow_status_on_fresh_repo(self):
        gitflow = GitFlow(self.repo)
        self.assertEquals([], gitflow.status())

    @copy_from_fixture('sample_repo')
    def test_gitflow_status_on_sample_repo(self):
        gitflow = GitFlow(self.repo)
        self.assertItemsEqual([
                ('master', '296586bb164c946cad10d37e82570f60e6348df9', False),
                ('develop', '2b34cd2e1617e5f0d4e077c6ec092b9f50ed49a3', False),
                ('feature/recursion', '54d59c872469c7bf34d540d2fb3128a97502b73f', True),
                ('feature/even', 'e56be18dada9e81ca7969760ddea357b0c4c9412', False),
            ], gitflow.status())


    # git flow init
    @sandboxed
    def test_gitflow_init_inits_underlying_git_repo(self):
        gitflow = GitFlow(self.sandbox)
        dot_git_dir = os.path.join(self.sandbox, '.git')
        self.assertFalse(os.path.exists(dot_git_dir))
        gitflow.init()
        self.assertTrue(os.path.exists(dot_git_dir))
        self.assertTrue(gitflow.is_initialized())

    @sandboxed_git_repo
    def test_gitflow_init_marks_initialized(self):
        gitflow = GitFlow(self.repo)
        self.assertFalse(gitflow.is_initialized())
        gitflow.init()
        self.assertTrue(gitflow.is_initialized())

    @sandboxed_git_repo
    def test_gitflow_throws_errors_before_init(self):
        gitflow = GitFlow(self.repo)
        self.assertRaises(NotInitialized, gitflow.master_name)
        self.assertRaises(NotInitialized, gitflow.develop_name)
        self.assertRaises(NotInitialized, gitflow.feature_prefix)
        self.assertRaises(NotInitialized, gitflow.hotfix_prefix)
        self.assertRaises(NotInitialized, gitflow.release_prefix)
        self.assertRaises(NotInitialized, gitflow.support_prefix)

    @sandboxed_git_repo
    def test_gitflow_init_initializes_default_config(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()
        self.assertEquals('master', gitflow.master_name())
        self.assertEquals('develop', gitflow.develop_name())
        self.assertEquals('feature/', gitflow.feature_prefix())
        self.assertEquals('hotfix/', gitflow.hotfix_prefix())
        self.assertEquals('release/', gitflow.release_prefix())
        self.assertEquals('support/', gitflow.support_prefix())

    @sandboxed_git_repo
    def test_gitflow_init_with_alternative_config(self):
        gitflow = GitFlow(self.repo)
        gitflow.init(master='foo', develop='bar', feature='f-', hotfix='hf-',
                release='rel-', support='supp-')
        self.assertEquals('foo', gitflow.master_name())
        self.assertEquals('bar', gitflow.develop_name())
        self.assertEquals('f-', gitflow.feature_prefix())
        self.assertEquals('hf-', gitflow.hotfix_prefix())
        self.assertEquals('rel-', gitflow.release_prefix())
        self.assertEquals('supp-', gitflow.support_prefix())

    @copy_from_fixture('partly_inited')
    def test_gitflow_init_config_with_partly_inited(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()

        # Already set in fixture, shouldn't change
        self.assertEquals('production', gitflow.master_name())
        self.assertEquals('f-', gitflow.feature_prefix())

        # Implicit defaults
        self.assertEquals('develop', gitflow.develop_name())
        self.assertEquals('hotfix/', gitflow.hotfix_prefix())
        self.assertEquals('release/', gitflow.release_prefix())
        self.assertEquals('support/', gitflow.support_prefix())

    @copy_from_fixture('sample_repo')
    def test_gitflow_init_creates_no_extra_commits(self):
        all_commits_before_init = self.all_commits(self.repo)
        gitflow = GitFlow(self.repo)
        gitflow.init()
        all_commits_after_init = self.all_commits(self.repo)
        self.assertEquals(all_commits_before_init, all_commits_after_init)

    @copy_from_fixture('sample_repo')
    def test_gitflow_init_creates_no_extra_branches(self):
        heads_before_init = [h.name for h in self.repo.heads]
        gitflow = GitFlow(self.repo)
        gitflow.init()
        heads_after_init = [h.name for h in self.repo.heads]
        self.assertItemsEqual(heads_before_init, heads_after_init)

    @sandboxed_git_repo
    def test_gitflow_init_creates_initial_commit(self):
        all_commits_before_init = self.all_commits(self.repo)
        gitflow = GitFlow(self.repo)
        gitflow.init()
        all_commits_after_init = self.all_commits(self.repo)
        self.assertNotEquals(all_commits_before_init, all_commits_after_init)
        self.assertEquals('Initial commit', self.repo.heads.master.commit.message)

    @sandboxed_git_repo
    def test_gitflow_init_creates_branches(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()
        self.assertItemsEqual(['master', 'develop'],
                gitflow.branch_names())

    @copy_from_fixture('partly_inited')
    def test_gitflow_force_reinit_partly_inited(self):
        gitflow = GitFlow(self.repo)
        gitflow.init(force_defaults=True)

        # Implicit defaults
        self.assertEquals('develop', gitflow.develop_name())
        self.assertEquals('hotfix/', gitflow.hotfix_prefix())
        self.assertEquals('release/', gitflow.release_prefix())
        self.assertEquals('support/', gitflow.support_prefix())

        # Explicitly forced back to defaults
        self.assertEquals('master', gitflow.master_name())
        self.assertEquals('feature/', gitflow.feature_prefix())


    # branch type detection
    @sandboxed_git_repo
    def test_detect_branch_types(self):
        gitflow = GitFlow()

        # The types that "ship" with git-flow
        self.assertIn('feature', gitflow.branch_types)
        self.assertIn('release', gitflow.branch_types)
        self.assertIn('hotfix', gitflow.branch_types)
        self.assertIn('support', gitflow.branch_types)

    @sandboxed_git_repo
    def test_detect_custom_branch_types(self):
        # Declare a custom branch type inline
        class FooBar(Branch):
            identifier = 'foobar'

        gitflow = GitFlow()
        self.assertIn('foobar', gitflow.branch_types)


    # git flow feature
    @sandboxed_git_repo
    def test_gitflow_empty_repo_has_no_features(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()
        self.assertItemsEqual([], gitflow.feature_branches())

    @copy_from_fixture('sample_repo')
    def test_gitflow_sample_repo_has_features(self):
        gitflow = GitFlow(self.repo)
        self.assertItemsEqual(['feature/even', 'feature/recursion'],
                gitflow.feature_branches())

    @sandboxed_git_repo
    def test_gitflow_create_feature_branch(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()
        gitflow.new_feature_branch('foo')
        branches = gitflow.feature_branches()
        self.assertIn('feature/foo', branches)

    @sandboxed_git_repo
    def test_gitflow_cannot_create_existing_feature(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()
        gitflow.new_feature_branch('foo')
        self.assertRaises(BranchExists, gitflow.new_feature_branch, 'foo')

    @copy_from_fixture('sample_repo')
    def test_gitflow_create_feature_from_alt_base(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()

        new_branch = gitflow.new_feature_branch('foo', 'feature/even')
        branches = gitflow.feature_branches()
        self.assertIn('feature/even', branches)
        self.assertIn('feature/foo', branches)
        self.assertEquals(self.repo.commit('feature/even'), new_branch.commit)

    @copy_from_fixture('sample_repo')
    def test_gitflow_create_feature_changes_active_branch(self):
        gitflow = GitFlow(self.repo)

        self.assertEquals('feature/recursion', self.repo.active_branch.name)
        gitflow.new_feature_branch('foo')
        self.assertEquals('feature/foo', self.repo.active_branch.name)

    @copy_from_fixture('dirty_sample_repo')
    def test_gitflow_create_feature_changes_active_branch_even_if_dirty_but_without_conflicts(self):
        gitflow = GitFlow(self.repo)
        # TODO: This should really be something like
        # self.repo.head.reset(paths=['odd.py'])
        self.repo.git.reset('-q', 'HEAD', '--', 'odd.py')
        self.repo.git.checkout('odd.py')
        gitflow.new_feature_branch('foo')
        self.assertIn('feature/foo', gitflow.feature_branches())


    @copy_from_fixture('dirty_sample_repo')
    def test_gitflow_cannot_create_feature_if_local_changes_would_be_overwritten(self):
        gitflow = GitFlow(self.repo)
        self.assertRaisesRegexp(GitCommandError,
                "Your local changes to the following files would be overwritten",
                gitflow.new_feature_branch, 'foo')

    @copy_from_fixture('sample_repo')
    def test_gitflow_delete_feature(self):
        gitflow = GitFlow(self.repo)

        self.assertIn('feature/even', gitflow.feature_branches())
        gitflow.delete_feature_branch('even')
        self.assertNotIn('feature/even', gitflow.feature_branches())

    @copy_from_fixture('sample_repo')
    def test_gitflow_cannot_delete_current_feature(self):
        gitflow = GitFlow(self.repo)
        self.assertRaisesRegexp(InvalidOperation, 'Cannot delete the branch .* '
                'which you are currently on',
                gitflow.delete_feature_branch, 'recursion')

    @copy_from_fixture('sample_repo')
    def test_gitflow_cannot_delete_non_existing_feature(self):
        gitflow = GitFlow(self.repo)
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

