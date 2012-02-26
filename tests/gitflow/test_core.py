from unittest2 import TestCase
import os
from ConfigParser import NoOptionError, NoSectionError
from gitflow.core import GitFlow, NotInitialized
from gitflow.branches import BranchManager
from tests.helpers import copy_from_fixture, remote_clone_from_fixture
from tests.helpers.factory import create_sandbox, create_git_repo

def all_commits(repo):
    s = set([])
    for h in repo.heads:
        s |= set(repo.iter_commits(h))
    return s


class TestGitFlow(TestCase):

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
    def test_branch_names_fails_in_new_sandbox(self):
        sandbox = create_sandbox(self)
        gitflow = GitFlow(sandbox)
        self.assertRaises(NotInitialized, gitflow.branch_names)

    def test_empty_repo_has_no_branches(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        self.assertItemsEqual([], gitflow.branch_names())

    @copy_from_fixture('custom_repo')
    def test_custom_repo_has_branches(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()
        self.assertItemsEqual(['master', 'production'],
                gitflow.branch_names())

    @copy_from_fixture('custom_repo')
    def test_custom_repo_init_keeps_active_branch_if_develop_already_existed(self):
        active_branch = self.repo.active_branch
        gitflow = GitFlow(self.repo)
        gitflow.init()
        self.assertNotEqual(gitflow.repo.active_branch.name, active_branch)

    # Sanity checking
    def test_new_repo_is_not_dirty(self):
        sandbox = create_sandbox(self)
        gitflow = GitFlow(sandbox)
        gitflow.init()
        self.assertFalse(gitflow.is_dirty())

    @copy_from_fixture('dirty_sample_repo')
    def test_existing_repo_is_not_dirty(self):
        gitflow = GitFlow(self.repo)
        self.assertTrue(gitflow.is_dirty())


    def test_gitflow_cannot_get_status_on_empty_sandbox(self):
        sandbox = create_sandbox(self)
        gitflow = GitFlow(sandbox)
        self.assertRaises(NotInitialized, gitflow.status)

    def test_gitflow_status_on_fresh_repo(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        self.assertEquals([], gitflow.status())

    @copy_from_fixture('sample_repo')
    def test_gitflow_status_on_sample_repo(self):
        gitflow = GitFlow(self.repo)
        self.assertItemsEqual([
                ('stable', '296586bb164c946cad10d37e82570f60e6348df9', False),
                ('devel', '2b34cd2e1617e5f0d4e077c6ec092b9f50ed49a3', False),
                ('feat/recursion', '54d59c872469c7bf34d540d2fb3128a97502b73f', True),
                ('feat/even', 'e56be18dada9e81ca7969760ddea357b0c4c9412', False),
            ], gitflow.status())


    # git flow init
    def test_gitflow_init_inits_underlying_git_repo(self):
        sandbox = create_sandbox(self)
        gitflow = GitFlow(sandbox)
        dot_git_dir = os.path.join(sandbox, '.git')
        self.assertFalse(os.path.exists(dot_git_dir))
        gitflow.init()
        self.assertTrue(os.path.exists(dot_git_dir))
        self.assertTrue(gitflow.is_initialized())

    def test_gitflow_init_marks_initialized(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        self.assertFalse(gitflow.is_initialized())
        gitflow.init()
        self.assertTrue(gitflow.is_initialized())

    def test_gitflow_throws_errors_before_init(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        self.assertRaises(NotInitialized, gitflow.master_name)
        self.assertRaises(NotInitialized, gitflow.develop_name)
        self.assertRaises(NotInitialized, gitflow.get_prefix, 'feature')

    def test_gitflow_init_initializes_default_config(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        gitflow.init()
        self.assertEquals('master', gitflow.master_name())
        self.assertEquals('develop', gitflow.develop_name())
        self.assertEquals('feature/', gitflow.get_prefix('feature'))
        self.assertEquals('hotfix/', gitflow.get_prefix('hotfix'))
        self.assertEquals('release/', gitflow.get_prefix('release'))
        self.assertEquals('support/', gitflow.get_prefix('support'))

    def test_gitflow_init_with_alternative_config(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
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
    def test_gitflow_init_keeps_active_branch_if_develop_already_existed(self):
        active_branch = self.repo.active_branch.name
        gitflow = GitFlow(self.repo)
        gitflow.init()
        self.assertEqual(gitflow.repo.active_branch.name, active_branch)

    def test_gitflow_init_checkout_develop_if_newly_created(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        gitflow.init()
        self.assertEqual(gitflow.repo.active_branch.name, 'develop')

    @copy_from_fixture('sample_repo')
    def test_gitflow_init_creates_no_extra_commits(self):
        all_commits_before_init = all_commits(self.repo)
        gitflow = GitFlow(self.repo)
        gitflow.init()
        all_commits_after_init = all_commits(self.repo)
        self.assertEquals(all_commits_before_init, all_commits_after_init)

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_init_cloned_creates_no_extra_commits(self):
        all_commits_before_init = all_commits(self.repo)
        gitflow = GitFlow(self.repo)
        gitflow.init()
        all_commits_after_init = all_commits(self.repo)
        self.assertEquals(all_commits_before_init, all_commits_after_init)

    @copy_from_fixture('sample_repo')
    def test_gitflow_init_creates_no_extra_branches(self):
        heads_before_init = [h.name for h in self.repo.heads]
        gitflow = GitFlow(self.repo)
        gitflow.init()
        heads_after_init = [h.name for h in self.repo.heads]
        self.assertItemsEqual(heads_before_init, heads_after_init)

    def test_gitflow_init_creates_initial_commit(self):
        repo = create_git_repo(self)
        all_commits_before_init = all_commits(repo)
        gitflow = GitFlow(repo)
        gitflow.init()
        all_commits_after_init = all_commits(repo)
        self.assertNotEquals(all_commits_before_init, all_commits_after_init)
        self.assertEquals('Initial commit', repo.heads.master.commit.message)

    def test_gitflow_init_creates_branches(self):
        repo = create_git_repo(self)
        gitflow = GitFlow(repo)
        gitflow.init()
        self.assertItemsEqual(['master', 'develop'],
                gitflow.branch_names())

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_init_cloned_creates_master_and_develop(self):
        heads_before_init = [h.name for h in self.repo.heads]
        self.assertNotIn('stable', heads_before_init)
        self.assertNotIn('devel', heads_before_init)
        gitflow = GitFlow(self.repo)
        gitflow.init()
        heads_after_init = [h.name for h in self.repo.heads]
        self.assertIn('stable', heads_after_init)
        self.assertIn('devel', heads_after_init)

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_init_cloned_creates_no_custom_master_and_develop(self):
        heads_before_init = [h.name for h in self.repo.heads]
        self.assertNotIn('foo', heads_before_init)
        self.assertNotIn('bar', heads_before_init)
        gitflow = GitFlow(self.repo)
        self.assertRaises(NotImplementedError,
                          gitflow.init, master='foo', develop='bar')

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_init_cloned_creates_branches_from_counterpart(self):
        remote =  GitFlow(self.remote)
        rmc0 = remote.master().commit
        rdc0 = remote.develop().commit

        gitflow = GitFlow(self.repo)
        gitflow.init()
        mc0 = gitflow.master().commit
        dc0 = gitflow.develop().commit

        # local and remote heads must be the same
        self.assertEqual(rmc0, mc0)
        self.assertEqual(rdc0, dc0)
        self.assertTrue(gitflow.master().tracking_branch())
        self.assertTrue(gitflow.develop().tracking_branch())
        self.assertEqual(gitflow.master().tracking_branch().name, 'origin/stable')
        self.assertEqual(gitflow.develop().tracking_branch().name, 'origin/devel')


    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_init_cloned_creates_no_extra_banches(self):
        heads_before_init = [h.name for h in self.repo.heads]
        heads_before_init.sort()
        gitflow = GitFlow(self.repo)
        gitflow.init()
        heads_after_init = [h.name for h in self.repo.heads]
        heads_after_init.remove('stable')
        heads_after_init.remove('devel')
        self.assertItemsEqual(heads_before_init, heads_after_init)

    @remote_clone_from_fixture('sample_repo')
    def test_gitflow_init_cloned_checkout_develop_if_newly_created(self):
        gitflow = GitFlow(self.repo)
        gitflow.init()
        self.assertEqual(gitflow.repo.active_branch.name, 'devel')

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
    def test_detect_branch_types(self):
        create_git_repo(self)
        gitflow = GitFlow()

        # The types that "ship" with git-flow
        self.assertIn('feature', gitflow.managers)
        self.assertIn('release', gitflow.managers)
        self.assertIn('hotfix', gitflow.managers)
        self.assertIn('support', gitflow.managers)

    def test_detect_custom_branch_types(self):
        create_git_repo(self)
        # Declare a custom branch type inline
        class FooBarManager(BranchManager):
            identifier = 'foobar'
            DEFAULT_PREFIX = 'xyz/'

        gitflow = GitFlow()
        self.assertIn('foobar', gitflow.managers)


    # Branch creation
    def test_create_branches(self):
        create_git_repo(self)
        gitflow = GitFlow()
        gitflow.init()
        gitflow.create('feature', 'foo', None, fetch=False)
        self.assertIn('feature/foo',
                [h.name for h in gitflow.repo.branches])
        gitflow.create('release', '1.0', None, fetch=False)
        self.assertIn('release/1.0',
                [h.name for h in gitflow.repo.branches])

    def test_create_branches_from_alt_base(self):
        create_git_repo(self)
        gitflow = GitFlow()
        gitflow.init()
        gitflow.create('feature', 'foo', 'master', fetch=False)
        self.assertIn('feature/foo',
                [h.name for h in gitflow.repo.branches])
        gitflow.repo.index.commit('Foo')
        gitflow.create('release', '1.0', 'feature/foo', fetch=False)
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

