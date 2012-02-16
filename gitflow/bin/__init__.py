#!/usr/bin/env python
"""
git-flow

.. program:: git flow

.. cmdoption:: -v, --verbose

       Produce more output.

.. cmdoption:: -h, --help

       Print usage, help and information on the available commands.

"""
import sys
import argparse
from gitflow.core import GitFlow
from gitflow.util import itersubclasses

def warn(*texts):
    for txt in texts:
        print >> sys.stderr, txt

def die(*texts):
    warn(*texts)
    raise SystemExit(1)

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


class VersionCommand(GitFlowCommand):
    def register_parser(self, parent):
        p = parent.add_parser('version', help='Show the version of gitflow.')
        p.set_defaults(func=self.run)

    def run(self, args):
        from gitflow import __version__
        print(__version__)


class InitCommand(GitFlowCommand):
    def register_parser(self, parent):
        p = parent.add_parser('init',
                              help='Initialize a repository for gitflow.')
        p.add_argument('-f', '--force', action='store_true',
                       help='force reinitialization of the gitflow preferences')
        p.add_argument('-d', '--defaults', action='store_true',
                       dest='use_defaults',
                       help='use default branch naming conventions and prefixes')
        p.set_defaults(func=self.run)
        return p

    def run(self, args):
        from . import _init
        _init.run_default(args)


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
        p.add_argument('-k', '--keep', action='store_true',
                help='Keep branch after performing finish.')
        p.add_argument('-D', '--force-delete', action='store_true',
                help='Force delete feature branch after finish.')
        p.add_argument('nameprefix', nargs='?')

        # publish
        p = sub.add_parser('publish',
                help='Publish this feature branch to origin.')
        p.set_defaults(func=self.run_publish)
        p.add_argument('nameprefix')

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
        gitflow = GitFlow()
        gitflow.start_transaction()
        manager = gitflow.managers['feature']
        branches = manager.list()
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
        width = max(map(lenfunc, branches)) - len(manager.prefix) + 3

        develop_sha = gitflow.develop().commit.hexsha

        for branch in branches:
            is_active = gitflow.repo.active_branch == branch
            if is_active:
                prefix = '* '
            else:
                prefix = '  '

            name = manager.shorten(branch.name)
            extra_info = ''

            if args.verbose:
                name = name.ljust(width)
                branch_sha = branch.commit.hexsha
                base_sha = gitflow.repo.git.merge_base(develop_sha, branch_sha)
                if branch_sha == develop_sha:
                    extra_info = '(no commits yet)'
                elif base_sha == branch_sha:
                    extra_info = '(is behind develop, may ff)'
                elif base_sha == develop_sha:
                    extra_info = '(based on latest develop)'
                else:
                    extra_info = '(may be rebased)'

            print(prefix + name + extra_info)

    def run_start(self, args):
        gitflow = GitFlow()
        gitflow.start_transaction('create feature branch %s (from %s)' % \
                (args.name, args.base))
        gitflow.create('feature', args.name, args.base)

    def run_finish(self, args):
        gitflow = GitFlow()
        gitflow.start_transaction('finishing feature branch %s'
                % args.nameprefix)
        gitflow.finish('feature', args.nameprefix)

    def run_publish(self, args): pass
    def run_track(self, args): pass
    def run_diff(self, args): pass
    def run_rebase(self, args): pass
    def run_checkout(self, args): pass
    def run_pull(self, args): pass


class ReleaseCommand(GitFlowCommand):
    def register_parser(self, parent):
        p = parent.add_parser('release', help='Manage your release branches.')
        p.add_argument('-v', '--verbose', action='store_true',
           help='be verbose (more output)')
        sub = p.add_subparsers(title='Actions')

        # list
        p = sub.add_parser('list', help='List all release branches.')
        p.set_defaults(func=self.run_list)
        p.add_argument('-v', '--verbose', action='store_true',
                help='Be verbose (more output).')

        # start
        p = sub.add_parser('start', help='Start a new release branch.')
        p.set_defaults(func=self.run_start)
        p.add_argument('-F', '--fetch', action='store_true',
                       #:todo: get "origin" from config
                help='Fetch from origin before performing local operation.')
        p.add_argument('version')
        p.add_argument('base', nargs='?')

        # finish
        p = sub.add_parser('finish', help='Finish a release branch.')
        p.set_defaults(func=self.run_finish)
        p.add_argument('-r', '--rebase', action='store_true',
                help='Finish branch by rebasing first.')
        p.add_argument('-F', '--fetch', action='store_true',
                help='Fetch from origin before performing local operation.')
        p.add_argument('-s', '--sign', action='store_true',
                help="sign the release tag cryptographically")
        p.add_argument('-u', '--signingkey',
                help="use the given GPG-key for the digital signature "
                     "(implies -s)")
        p.add_argument('-m', '--message',
                       help="use the given tag message")
        p.add_argument('-p', '--push', action='store_true',
                       #:todo: get "origin" from config
                       help="push to origin after performing finish")
        p.add_argument('-k', '--keep', action='store_true',
                help='Keep branch after performing finish.')
        p.add_argument('-n', '--notag', action='store_true',
                       help="don't tag this release")
        p.add_argument('version')

        # publish
        p = sub.add_parser('publish',
                help='Publish this release branch to origin.')
        p.set_defaults(func=self.run_publish)
        p.add_argument('version')

        # track
        p = sub.add_parser('track',
                help='Track a release branch from origin.')
        p.set_defaults(func=self.run_track)
        p.add_argument('version')


    def run_list(self, args): pass
    def run_start(self, args): pass
    def run_finish(self, args): pass
    def run_publish(self, args): pass
    def run_track(self, args): pass


class HotfixCommand(GitFlowCommand):
    def register_parser(self, parent):
        p = parent.add_parser('hotfix', help='Manage your hotfix branches.')
        p.add_argument('-v', '--verbose', action='store_true',
           help='be verbose (more output)')
        sub = p.add_subparsers(title='Actions')

        # list
        p = sub.add_parser('list', help='List all hotfix branches.')
        p.set_defaults(func=self.run_list)
        p.add_argument('-v', '--verbose', action='store_true',
                help='Be verbose (more output).')

        # start
        p = sub.add_parser('start', help='Start a new hotfix branch.')
        p.set_defaults(func=self.run_start)
        p.add_argument('-F', '--fetch', action='store_true',
                       #:todo: get "origin" from config
                help='Fetch from origin before performing local operation.')
        p.add_argument('version')
        p.add_argument('base', nargs='?')

        # finish
        p = sub.add_parser('finish', help='Finish a hotfix branch.')
        p.set_defaults(func=self.run_finish)
        p.add_argument('-r', '--rebase', action='store_true',
                help='Finish branch by rebasing first.')
        p.add_argument('-F', '--fetch', action='store_true',
                help='Fetch from origin before performing local operation.')
        p.add_argument('-s', '--sign', action='store_true',
                help="sign the hotfix tag cryptographically")
        p.add_argument('-u', '--signingkey',
                help="use the given GPG-key for the digital signature "
                     "(implies -s)")
        p.add_argument('-m', '--message',
                       help="use the given tag message")
        p.add_argument('-p', '--push', action='store_true',
                       #:todo: get "origin" from config
                       help="push to origin after performing finish")
        p.add_argument('-k', '--keep', action='store_true',
                help='Keep branch after performing finish.')
        p.add_argument('-n', '--notag', action='store_true',
                       help="don't tag this hotfix")
        p.add_argument('version')

        # publish
        p = sub.add_parser('publish',
                help='Publish this hotfix branch to origin.')
        p.set_defaults(func=self.run_publish)
        p.add_argument('version')

    def run_list(self, args): pass
    def run_start(self, args): pass
    def run_finish(self, args): pass
    def run_publish(self, args): pass


class SupportCommand(GitFlowCommand):
    def register_parser(self, parent):
        p = parent.add_parser('support', help='Manage your support branches.')
        p.add_argument('-v', '--verbose', action='store_true',
           help='be verbose (more output)')
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


    def run_list(self, args): pass
    def run_start(self, args): pass

def main():
    parser = argparse.ArgumentParser(prog='git flow')
    placeholder = parser.add_subparsers(title='Subcommands')
    for cls in itersubclasses(GitFlowCommand):
        cls().register_parser(placeholder)
    args = parser.parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        die('', 'Aborted by user request.')


if __name__ == '__main__':
    main()
