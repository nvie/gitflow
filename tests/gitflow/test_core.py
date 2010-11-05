from unittest2 import TestCase, skip
import os
import tempfile
import datetime
from ConfigParser import NoOptionError, NoSectionError
from git import Repo, GitCommandError
import shutil
from gitflow.core import GitFlow, NotInitialized, BranchExists, InvalidOperation
from gitflow.core import Snapshot
from gitflow.branches import BranchManager
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
        self.assertEquals('f-', gitflow.get_prefix('feature'))
        self.assertEquals('rel-', gitflow.get_prefix('release'))
        self.assertEquals('hf-', gitflow.get_prefix('hotfix'))
        self.assertEquals('supp-', gitflow.get_prefix('support'))


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
        self.assertRaises(NotInitialized, gitflow.get_prefix, 'feature')

    @sandboxed_git_repo
    def test_gitflow_init_initializes_default_config(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()
        self.assertEquals('master', gitflow.master_name())
        self.assertEquals('develop', gitflow.develop_name())
        self.assertEquals('feature/', gitflow.get_prefix('feature'))
        self.assertEquals('hotfix/', gitflow.get_prefix('hotfix'))
        self.assertEquals('release/', gitflow.get_prefix('release'))
        self.assertEquals('support/', gitflow.get_prefix('support'))

    @sandboxed_git_repo
    def test_gitflow_init_with_alternative_config(self):
        gitflow = GitFlow(self.repo)
        prefixes = dict(feature='f-', hotfix='hf-', release='rel-', support='supp-')
        gitflow.init(master='foo', develop='bar', prefixes=prefixes)
        self.assertEquals('foo', gitflow.master_name())
        self.assertEquals('bar', gitflow.develop_name())
        self.assertEquals('f-', gitflow.get_prefix('feature'))
        self.assertEquals('rel-', gitflow.get_prefix('release'))
        self.assertEquals('hf-', gitflow.get_prefix('hotfix'))
        self.assertEquals('supp-', gitflow.get_prefix('support'))

    @copy_from_fixture('partly_inited')
    def test_gitflow_init_config_with_partly_inited(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()

        # Already set in fixture, shouldn't change
        self.assertEquals('production', gitflow.master_name())
        self.assertEquals('f-', gitflow.get_prefix('feature'))

        # Implicit defaults
        self.assertEquals('develop', gitflow.develop_name())
        self.assertEquals('release/', gitflow.get_prefix('release'))
        self.assertEquals('hotfix/', gitflow.get_prefix('hotfix'))
        self.assertEquals('support/', gitflow.get_prefix('support'))

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
        self.assertEquals('release/', gitflow.get_prefix('release'))
        self.assertEquals('hotfix/', gitflow.get_prefix('hotfix'))
        self.assertEquals('support/', gitflow.get_prefix('support'))

        # Explicitly forced back to defaults
        self.assertEquals('master', gitflow.master_name())
        self.assertEquals('feature/', gitflow.get_prefix('feature'))


    # branch type detection
    @sandboxed_git_repo
    def test_detect_branch_types(self):
        gitflow = GitFlow()

        # The types that "ship" with git-flow
        self.assertIn('feature', gitflow.managers)
        self.assertIn('release', gitflow.managers)
        self.assertIn('hotfix', gitflow.managers)
        self.assertIn('support', gitflow.managers)

    @sandboxed_git_repo
    def test_detect_custom_branch_types(self):
        # Declare a custom branch type inline
        class FooBarManager(BranchManager):
            identifier = 'foobar'
            prefix = 'xyz/'

        gitflow = GitFlow()
        self.assertIn('foobar', gitflow.managers)


    # branch creation
    @sandboxed_git_repo
    def test_create_branches(self):
        gitflow = GitFlow()
        gitflow.init()
        gitflow.create('feature', 'foo')
        self.assertIn('feature/foo',
                [h.name for h in gitflow.repo.branches])
        gitflow.create('release', '1.0')
        self.assertIn('release/1.0',
                [h.name for h in gitflow.repo.branches])

    @sandboxed_git_repo
    def test_create_branches_from_alt_base(self):
        gitflow = GitFlow()
        gitflow.init()
        gitflow.create('feature', 'foo', 'master')
        self.assertIn('feature/foo',
                [h.name for h in gitflow.repo.branches])
        gitflow.repo.index.commit('Foo')
        gitflow.create('release', '1.0', 'feature/foo')
        self.assertIn('release/1.0',
                [h.name for h in gitflow.repo.branches])


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


class TestSnapshot(TestCase):
    @copy_from_fixture('sample_repo')
    def test_create(self):
        gitflow = GitFlow()

        now = datetime.datetime.now()
        s = Snapshot(gitflow, now, 'Some message')
        self.assertEquals(s.date, now)
        self.assertEquals(s.description, 'Some message')

        # Just test for a single branch's existence here
        tup = ('develop', '2b34cd2e1617e5f0d4e077c6ec092b9f50ed49a3', False)
        self.assertIn(tup, s.state)

    @copy_from_fixture('sample_repo')
    def test_read_write(self):
        gitflow = GitFlow()

        # Write the snapshot to disk
        now = datetime.datetime.now()
        s = Snapshot(gitflow, now, 'Some message')
        s.write()

        git_dir = gitflow.repo.git_dir
        undofile = os.path.join(git_dir, 'gitflow.undo')
        self.assertTrue(os.path.exists(undofile))

        contents = open(undofile, 'r').read()
        found = contents.find('2b34cd2e1617e5f0d4e077c6ec092b9f50ed49a3') >= 0
        self.assertTrue(found)

        # Read it in again and compare the Snapshot objects
        s2 = Snapshot.read(gitflow)
        self.assertEquals(s, s2)
