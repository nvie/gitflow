from unittest2 import TestCase, skip
import os
import datetime
import ConfigParser
from ConfigParser import NoOptionError, NoSectionError
from gitflow.core import GitFlow, NotInitialized
from gitflow.core import Snapshot
from gitflow.branches import BranchManager
from tests.helpers import sandboxed, sandboxed_git_repo, copy_from_fixture

class TestSnapshot(TestCase):
    @copy_from_fixture('sample_repo')
    def test_create(self):
        gitflow = GitFlow()

        now = datetime.datetime.now()
        s = Snapshot(gitflow, 'Some message', now)
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

        config = ConfigParser.ConfigParser()

        s = Snapshot(gitflow, 'Some message', now)
        s.write(config, 0)

        # Test contents
        self.assertEquals('2b34cd2e1617e5f0d4e077c6ec092b9f50ed49a3',
                config.get('heads0', 'develop'))

        # Read it in again and compare the Snapshot objects
        s2 = Snapshot.read(gitflow, config, 0)
        self.assertEquals(s, s2)


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


    # Branch type detection
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


    # Branch creation
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


    # Snapshots
    @sandboxed_git_repo
    def test_empty_repo_has_empty_snapshot_stack(self):
        gitflow = GitFlow()
        gitflow.init()
        self.assertEquals([], gitflow.snapshots())

    @copy_from_fixture('sample_repo')
    def test_make_snapshot_increases_stack_size(self):
        gitflow = GitFlow()
        gitflow.snap('Some message')
        self.assertEquals(1, len(gitflow.snapshots()))

    @copy_from_fixture('sample_repo')
    def test_snapshot_writes_ini_file(self):
        gitflow = GitFlow()
        gitflow.snap('Some message')
        self.assertTrue(os.path.exists('.git/snapshots'))

        cfg = ConfigParser.ConfigParser()
        cfg.read('.git/snapshots')
        self.assertEquals('Some message', cfg.get('meta0', 'description'))

    @copy_from_fixture('sample_repo')
    def test_snapshot_read_from_ini_file(self):
        gitflow = GitFlow()
        gitflow.snap('Some message')

        new_gitflow = GitFlow()
        new_gitflow.snapshots()
        self.assertEquals(1, len(new_gitflow.snapshots()))


    # Restore
    @copy_from_fixture('sample_repo')
    def test_restore_snapshot(self):
        gitflow = GitFlow()
        snap = gitflow.snap('Some message')

        orig_develop_sha = gitflow.develop().commit.hexsha
        orig_master_sha = gitflow.master().commit.hexsha

        gitflow.create('release', '1.0')
        gitflow.repo.index.commit('Foo')
        gitflow.repo.index.commit('Bar')
        gitflow.finish('release', '1.0')

        gitflow.restore(snap, backup=False)

        self.assertEquals(orig_develop_sha, gitflow.develop().commit.hexsha)
        self.assertEquals(orig_master_sha, gitflow.master().commit.hexsha)

    @copy_from_fixture('sample_repo')
    def test_restore_snapshot_with_backup(self):
        gitflow = GitFlow()
        snap = gitflow.snap('Some message')

        gitflow.create('release', '1.0')
        gitflow.repo.index.commit('Foo')
        gitflow.repo.index.commit('Bar')
        gitflow.finish('release', '1.0')

        develop_sha_before_restore = gitflow.develop().commit.hexsha
        master_sha_before_restore = gitflow.master().commit.hexsha

        gitflow.restore(snap, backup=True)

        self.assertEquals(develop_sha_before_restore,
                gitflow.repo.branches['backup/develop'].commit.hexsha)
        self.assertEquals(master_sha_before_restore,
                gitflow.repo.branches['backup/master'].commit.hexsha)


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

