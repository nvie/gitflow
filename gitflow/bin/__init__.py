#!/usr/bin/env python
"""
git-flow

.. program:: git flow

.. cmdoption:: -v, --verbose

       Produce more output.

.. cmdoption:: -h, --help

       Print usage, help and information on the available commands.

"""
import argparse
from gitflow.util import itersubclasses


class GitFlowCommand(object):
    """
    This is just an empty class to serve as the base class for all command line
    level sub commands.  Since the git-flow loader will auto-detect all
    subclasses, implementing a new subcommand is as easy as subclassing the
    :class:`GitFlowCommand`.
    """
    def register_parser(self, parent):
        raise NotImplementedError("Implement this method in a subclass.")

    def run(self, args):
        raise NotImplementedError("Implement this method in a subclass.")


class InitCommand(GitFlowCommand):
    def register_parser(self, parent):
        p = parent.add_parser('init',
                help='Initialize a repository for gitflow.')
        p.add_argument('-f', '--force', action='store_true',
                help='force reinitialization of the gitflow preferences')
        p.set_defaults(func=self.run)
        return p

    def run(self, args):
        print('-------------------')
        print('Init has been run!')
        print(args)
        print('-------------------')


class ReleaseCommand(GitFlowCommand):
    def register_parser(self, parent):
        p = parent.add_parser('release', help='Manage your release branches.')
        p.add_argument('-v', '--verbose', action='store_true',
           help='be verbose (more output)')
        p.set_defaults(func=self.run)
        return p

    def run(self, args):
        print 'release ran'
        print(args)


class FeatureCommand(GitFlowCommand):
    def register_parser(self, parent):
        p = parent.add_parser('feature', help='Manage your feature branches.')
        sub = p.add_subparsers(title='Actions')

        # list
        p = sub.add_parser('list', help='List all feature branches.')
        p.set_defaults(func=self.run_list)
        p.add_argument('-v', '--verbose', action='store_true',
                help='Be verbose (more output).')

        # start
        p = sub.add_parser('start', help='Start a new feature branch.')
        p.set_defaults(func=self.run_start)
        p.add_argument('-F', '--fetch', action='store_true',
                help='Fetch from origin before performing local operation.')
        p.add_argument('name')
        p.add_argument('base', nargs='?')

        # finish
        p = sub.add_parser('finish', help='Finish a feature branch.')
        p.set_defaults(func=self.run_finish)
        p.add_argument('-r', '--rebase', action='store_true',
                help='Finish branch by rebasing first.')
        p.add_argument('-F', '--fetch', action='store_true',
                help='Fetch from origin before performing local operation.')
        p.add_argument('nameprefix')

        # publish
        p = sub.add_parser('publish',
                help='Publish this feature branch to origin.')
        p.set_defaults(func=self.run_publish)
        p.add_argument('name')

        # track
        p = sub.add_parser('track',
                help='Track a feature branch from origin.')
        p.set_defaults(func=self.run_track)
        p.add_argument('name')

        # diff
        p = sub.add_parser('diff',
                help='Show a diff of changes since this feature branched off.')
        p.set_defaults(func=self.run_diff)
        p.add_argument('nameprefix', nargs='?')

        # rebase
        p = sub.add_parser('rebase',
                help='Rebase a feature branch on top of develop.')
        p.set_defaults(func=self.run_rebase)
        p.add_argument('-i', '--interactive', action='store_true',
                help='Start an interactive rebase.')
        p.add_argument('nameprefix', nargs='?')

        # checkout
        p = sub.add_parser('checkout',
                help='Check out the given feature branch.')
        p.set_defaults(func=self.run_checkout)
        p.add_argument('nameprefix')

        # pull
        p = sub.add_parser('pull',
                help='Pull a feature branch from a remote peer.')
        p.set_defaults(func=self.run_pull)
        p.add_argument('remote')
        p.add_argument('name', nargs='?')

    def run_list(self, args):
        require_gitflow_initialized()
        branches = feature_branches()
        if not branches:
            warn('No feature branches exist.')
            warn('')
            warn('You can start a new feature branch:')
            warn('')
            warn('    git flow feature start <name> [<base>]')
            warn('')
            raise SystemExit()

        # determine the longest branch name
        lenfunc = lambda b: len(b.name)
        width = max(map(lenfunc, branches)) + 3

        # lookup the SHA's that don't change
        g = Git()
        develop_commit = develop_branch().object
        develop_sha = develop_commit.hexsha

        for branch in branches:
            is_active = get_repo().active_branch.name == branch.fullname
            prefix = '  '
            if is_active:
                prefix = '* '

            name = branch.name
            extra_info = ''

            if args.verbose:
                name = name.ljust(width)
                commit = branch.branch.object
                branch_sha = commit.hexsha
                base_sha = g.merge_base(develop_sha, branch_sha)
                if branch_sha == develop_sha:
                    extra_info = '(no commits yet)'
                elif base_sha == branch_sha:
                    extra_info = '(is behind develop, may ff)'
                elif base_sha == develop_sha:
                    extra_info = '(based on latest develop)'
                else:
                    extra_info = '(may be rebased)'

            print(prefix + name + extra_info)

    def run_start(self, args): pass
    def run_finish(self, args): pass
    def run_publish(self, args): pass
    def run_track(self, args): pass
    def run_diff(self, args): pass
    def run_rebase(self, args): pass
    def run_checkout(self, args): pass
    def run_pull(self, args): pass


class VersionCommand(GitFlowCommand):
    def register_parser(self, parent):
        p = parent.add_parser('version', help='Show the version of gitflow.')
        p.set_defaults(func=self.run)

    def run(self, args):
        from gitflow import __version__
        print(__version__)


def main():
    parser = argparse.ArgumentParser(prog='git flow')
    placeholder = parser.add_subparsers(title='Subcommands')
    for cls in itersubclasses(GitFlowCommand):
        cls().register_parser(placeholder)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
