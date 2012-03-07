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

from gitflow.core import GitFlow, info
from gitflow.util import itersubclasses
from gitflow.exceptions import (GitflowError, AlreadyInitialized,
                                NotInitialized, BranchTypeExistsError,
                                BaseNotOnBranch)

def die(*texts):
    raise SystemExit('\n'.join(map(str, texts)))

class NotEmpty(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not values:
            raise argparse.ArgumentError(self, 'must not by empty.')
        setattr(namespace, self.dest, values)


class GitFlowCommand(object):
    """
    This is just an empty class to serve as the base class for all command line
    level sub commands.  Since the git-flow loader will auto-detect all
    subclasses, implementing a new subcommand is as easy as subclassing the
    :class:`GitFlowCommand`.
    """
    @classmethod
    def register_parser(cls, parent):
        raise NotImplementedError("Implement this method in a subclass.")

    @staticmethod
    def run(args):
        raise NotImplementedError("Implement this method in a subclass.")


class VersionCommand(GitFlowCommand):
    @classmethod
    def register_parser(cls, parent):
        p = parent.add_parser('version', help='Show the version of gitflow.')
        p.set_defaults(func=cls.run)

    @staticmethod
    def run(args):
        from gitflow import __version__
        print(__version__)


class StatusCommand(GitFlowCommand):
    @classmethod
    def register_parser(cls, parent):
        p = parent.add_parser('status', help='Show some status.')
        p.set_defaults(func=cls.run)

    @staticmethod
    def run(args):
        gitflow = GitFlow()
        for name, hexsha, is_active_branch in gitflow.status():
            if is_active_branch:
                prefix = '*'
            else:
                prefix = ' '
            info('%s %s: %s' % (prefix, name, hexsha[:7]))


class InitCommand(GitFlowCommand):
    @classmethod
    def register_parser(cls, parent):
        p = parent.add_parser('init',
                              help='Initialize a repository for gitflow.')
        p.add_argument('-f', '--force', action='store_true',
                       help='force reinitialization of the gitflow preferences')
        p.add_argument('-d', '--defaults', action='store_true',
                       dest='use_defaults',
                       help='use default branch naming conventions and prefixes')
        p.set_defaults(func=cls.run)
        return p

    @staticmethod
    def run(args):
        from . import _init
        _init.run_default(args)


class FeatureCommand(GitFlowCommand):
    @classmethod
    def register_parser(cls, parent):
        p = parent.add_parser('feature', help='Manage your feature branches.')
        sub = p.add_subparsers(title='Actions')
        cls.register_list(sub)
        cls.register_start(sub)
        cls.register_finish(sub)
        cls.register_publish(sub)
        cls.register_track(sub)
        cls.register_diff(sub)
        cls.register_rebase(sub)
        cls.register_checkout(sub)
        cls.register_pull(sub)

    #- list
    @classmethod
    def register_list(cls, parent):
        p = parent.add_parser('list', help='List all feature branches.')
        p.set_defaults(func=cls.run_list)
        p.add_argument('-v', '--verbose', action='store_true',
                help='Be verbose (more output).')

    @staticmethod
    def run_list(args):
        gitflow = GitFlow()
        gitflow.start_transaction()
        gitflow.list('feature', 'name', use_tagname=False,
                     verbose=args.verbose)

    #- start
    @classmethod
    def register_start(cls, parent):
        p = parent.add_parser('start', help='Start a new feature branch.')
        p.set_defaults(func=cls.run_start)
        p.add_argument('-F', '--fetch', action='store_true',
                help='Fetch from origin before performing local operation.')
        p.add_argument('name', action=NotEmpty)
        p.add_argument('base', nargs='?')

    @staticmethod
    def run_start(args):
        gitflow = GitFlow()
        # :fixme: Why does the sh-version not require a clean working dir?
        # NB: `args.name` is required since the branch must not yet exist
        # :fixme: get default value for `base`
        gitflow.start_transaction('create feature branch %s (from %s)' % \
                (args.name, args.base))
        try:
            branch = gitflow.create('feature', args.name, args.base,
                                    fetch=args.fetch)
        except Exception, e:
            die("Could not create feature branch %r" % args.name,
                str(e))
        print
        print "Summary of actions:"
        print "- A new branch", branch, "was created, based on", args.base
        print "- You are now on branch", branch
        print ""
        print "Now, start committing on your feature. When done, use:"
        print ""
        print "     git flow feature finish", args.name
        print

    #- finish
    @classmethod
    def register_finish(cls, parent):
        p = parent.add_parser('finish', help='Finish a feature branch.')
        p.set_defaults(func=cls.run_finish)
        p.add_argument('-F', '--fetch', action='store_true',
                help='Fetch from origin before performing local operation.')
        p.add_argument('-r', '--rebase', action='store_true',
                help='Finish branch by rebasing first.')
        p.add_argument('-k', '--keep', action='store_true',
                help='Keep branch after performing finish.')
        p.add_argument('-D', '--force-delete', action='store_true',
                help='Force delete feature branch after finish.')
        p.add_argument('nameprefix', nargs='?')

    @staticmethod
    def run_finish(args):
        gitflow = GitFlow()
        gitflow.start_transaction('finishing feature branch %s'
                % args.nameprefix)
        gitflow.finish('feature', args.nameprefix)

    #- publish
    @classmethod
    def register_publish(cls, parent):
        p = parent.add_parser('publish',
                help='Publish this feature branch to origin.')
        p.set_defaults(func=cls.run_publish)
        p.add_argument('nameprefix', nargs='?')

    @staticmethod
    def run_publish(args):
        gitflow = GitFlow()
        name = gitflow.nameprefix_or_current('feature', args.nameprefix)
        gitflow.start_transaction('publishing feature branch %s' % name)
        branch = gitflow.publish('feature', name)
        print
        print "Summary of actions:"
        print "- A new remote branch '%s' was created" % branch
        print "- The local branch '%s' was configured to track the remote branch" % branch
        print "- You are now on branch '%s'" % branch
        print

    #- track
    @classmethod
    def register_track(cls, parent):
        p = parent.add_parser('track',
                help='Track a feature branch from origin.')
        p.set_defaults(func=cls.run_track)
        p.add_argument('name', action=NotEmpty)

    @staticmethod
    def run_track(args):
        gitflow = GitFlow()
        # NB: `args.name` is required since the branch must not yet exist
        gitflow.start_transaction('tracking remote feature branch %s'
                                  % args.name)
        branch = gitflow.track('feature', args.name)
        print
        print "Summary of actions:"
        print "- A new remote tracking branch '%s' was created" % branch
        print "- You are now on branch '%s'" % branch
        print

    #- diff
    @classmethod
    def register_diff(cls, parent):
        p = parent.add_parser('diff',
                help='Show a diff of changes since this feature branched off.')
        p.set_defaults(func=cls.run_diff)
        p.add_argument('nameprefix', nargs='?')

    @staticmethod
    def run_diff(args):
        gitflow = GitFlow()
        name = gitflow.nameprefix_or_current('feature', args.nameprefix)
        gitflow.start_transaction('diff for feature branch %s' % name)
        gitflow.diff('feature', name)


    #- rebase
    @classmethod
    def register_rebase(cls, parent):
        p = parent.add_parser('rebase',
                help='Rebase a feature branch on top of develop.')
        p.set_defaults(func=cls.run_rebase)
        p.add_argument('-i', '--interactive', action='store_true',
                help='Start an interactive rebase.')
        p.add_argument('nameprefix', nargs='?')

    @staticmethod
    def run_rebase(args):
        gitflow = GitFlow()
        name = gitflow.nameprefix_or_current('feature', args.nameprefix)
        gitflow.start_transaction('rebasing feature branch %s' % name)
        gitflow.rebase('feature', name, args.interactive)

    #- checkout
    @classmethod
    def register_checkout(cls, parent):
        p = parent.add_parser('checkout',
                help='Check out (switch to) the given feature branch.')
        p.set_defaults(func=cls.run_checkout)
        p.add_argument('nameprefix', action=NotEmpty)

    @staticmethod
    def run_checkout(args):
        gitflow = GitFlow()
        # NB: Does not default to the current branch as `nameprefix` is required
        name = gitflow.nameprefix_or_current('feature', args.nameprefix)
        gitflow.start_transaction('checking out feature branch %s' % name)
        gitflow.checkout('feature', name)

    #- pull
    @classmethod
    def register_pull(cls, parent):
        p = parent.add_parser('pull',
                help='Pull a feature branch from a remote peer.')
        p.set_defaults(func=cls.run_pull)
        p.add_argument('remote', action=NotEmpty,
                       help="Remote repository to pull from.")
        p.add_argument('name', nargs='?',
                help='Name of the feature branch to pull. '
                'Defaults to the current branch, if it is a feature branch.')
        # :todo: implement --prefix
        #p.add-argument('-p', '--prefix',
        #               help='alternative remote feature branch name prefix')

    @staticmethod
    def run_pull(args):
        gitflow = GitFlow()
        name = gitflow.name_or_current('feature', args.name, must_exist=False)
        gitflow.start_transaction('pulling remote feature branch %s '
                                  'into local banch %s' % (args.remote, name))
        gitflow.pull('feature', args.remote, name)


class ReleaseCommand(GitFlowCommand):
    @classmethod
    def register_parser(cls, parent):
        p = parent.add_parser('release', help='Manage your release branches.')
        p.add_argument('-v', '--verbose', action='store_true',
           help='be verbose (more output)')
        sub = p.add_subparsers(title='Actions')
        cls.register_list(sub)
        cls.register_start(sub)
        cls.register_finish(sub)
        cls.register_publish(sub)
        cls.register_track(sub)

    #- list
    @classmethod
    def register_list(cls, parent):
        p = parent.add_parser('list', help='List all release branches.')
        p.set_defaults(func=cls.run_list)
        p.add_argument('-v', '--verbose', action='store_true',
                help='Be verbose (more output).')

    @staticmethod
    def run_list(args):
        gitflow = GitFlow()
        gitflow.start_transaction()
        gitflow.list('release', 'version', use_tagname=True,
                     verbose=args.verbose)

    #- start
    @classmethod
    def register_start(cls, parent):
        p = parent.add_parser('start', help='Start a new release branch.')
        p.set_defaults(func=cls.run_start)
        p.add_argument('-F', '--fetch', action='store_true',
                       #:todo: get "origin" from config
                help='Fetch from origin before performing local operation.')
        p.add_argument('version', action=NotEmpty)
        p.add_argument('base', nargs='?')

    @staticmethod
    def run_start(args):
        gitflow = GitFlow()
        # NB: `args.version` is required since the branch must not yet exist
        # :fixme: get default value for `base`
        gitflow.start_transaction('create release branch %s (from %s)' % \
                (args.version, args.base))
        try:
            branch = gitflow.create('release', args.version, args.base,
                                    fetch=args.fetch)
        except BranchTypeExistsError:
            # printed in main()
            raise
        except Exception, e:
            die("Could not create release branch %r" % args.version,
                str(e))
        print "Follow-up actions:"
        print "- Bump the version number now!"
        print "- Start committing last-minute fixes in preparing your release"
        print "- When done, run:"
        print
        print "     git flow release finish", args.version

    #- finish
    @classmethod
    def register_finish(cls, parent):
        p = parent.add_parser('finish', help='Finish a release branch.')
        p.set_defaults(func=cls.run_finish)
        p.add_argument('-F', '--fetch', action='store_true',
                help='Fetch from origin before performing local operation.')
        p.add_argument('-r', '--rebase', action='store_true',
                help='Finish branch by rebasing first.')
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

    @staticmethod
    def run_finish(args):
        pass

    #- publish
    @classmethod
    def register_publish(cls, parent):
        p = parent.add_parser('publish',
                help='Publish this release branch to origin.')
        p.set_defaults(func=cls.run_publish)
        p.add_argument('version', nargs='?')

    @staticmethod
    def run_publish(args):
        gitflow = GitFlow()
        version = gitflow.name_or_current('release', args.version)
        gitflow.start_transaction('publishing release branch %s' % version)
        branch = gitflow.publish('release', args.version)
        print
        print "Summary of actions:"
        print "- A new remote branch '%s' was created" % branch
        print "- The local branch '%s' was configured to track the remote branch" % branch
        print "- You are now on branch '%s'" % branch
        print

    #- track
    @classmethod
    def register_track(cls, parent):
        p = parent.add_parser('track',
                help='Track a release branch from origin.')
        p.set_defaults(func=cls.run_track)
        p.add_argument('version', action=NotEmpty)

    @staticmethod
    def run_track(args):
        gitflow = GitFlow()
        # NB: `args.version` is required since the branch must not yet exist
        gitflow.start_transaction('tracking remote release branch %s'
                                  % args.version)
        branch = gitflow.track('release', args.version)
        print
        print "Summary of actions:"
        print "- A new remote tracking branch '%s' was created" % branch
        print "- You are now on branch '%s'" % branch
        print


class HotfixCommand(GitFlowCommand):
    @classmethod
    def register_parser(cls, parent):
        p = parent.add_parser('hotfix', help='Manage your hotfix branches.')
        p.add_argument('-v', '--verbose', action='store_true',
           help='be verbose (more output)')
        sub = p.add_subparsers(title='Actions')
        cls.register_list(sub)
        cls.register_start(sub)
        cls.register_finish(sub)
        cls.register_publish(sub)

    #- list
    @classmethod
    def register_list(cls, parent):
        p = parent.add_parser('list', help='List all hotfix branches.')
        p.set_defaults(func=cls.run_list)
        p.add_argument('-v', '--verbose', action='store_true',
                help='Be verbose (more output).')

    @staticmethod
    def run_list(args):
        gitflow = GitFlow()
        gitflow.start_transaction()
        gitflow.list('hotfix', 'version', use_tagname=True,
                     verbose=args.verbose)

    #- start
    @classmethod
    def register_start(cls, parent):
        p = parent.add_parser('start', help='Start a new hotfix branch.')
        p.set_defaults(func=cls.run_start)
        p.add_argument('-F', '--fetch', action='store_true',
                       #:todo: get "origin" from config
                help='Fetch from origin before performing local operation.')
        p.add_argument('version', action=NotEmpty)
        p.add_argument('base', nargs='?')

    @staticmethod
    def run_start(args):
        gitflow = GitFlow()
        # NB: `args.version` is required since the branch must not yet exist
        # :fixme: get default value for `base`
        gitflow.start_transaction('create hotfix branch %s (from %s)' % \
                (args.version, args.base))
        try:
            branch = gitflow.create('hotfix', args.version, args.base,
                                    fetch=args.fetch)
        except BranchTypeExistsError:
            # printed in main()
            raise
        except Exception, e:
            die("Could not create hotfix branch %r" % args.version,
                str(e))
        print
        print "Summary of actions:"
        print "- A new branch", branch, "was created, based on", args.base
        print "- You are now on branch", branch
        print ""
        print "Follow-up actions:"
        print "- Bump the version number now!"
        print "- Start committing your hot fixes"
        print "- When done, run:"
        print
        print "     git flow hotfix finish", args.version

    #- finish
    @classmethod
    def register_finish(cls, parent):
        pass
        p = parent.add_parser('finish', help='Finish a hotfix branch.')
        p.set_defaults(func=cls.run_finish)
        p.add_argument('-F', '--fetch', action='store_true',
                help='Fetch from origin before performing local operation.')
        p.add_argument('-r', '--rebase', action='store_true',
                help='Finish branch by rebasing first.')
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

    @staticmethod
    def run_finish(args):
        pass

    #- publish
    @classmethod
    def register_publish(cls, parent):
        p = parent.add_parser('publish',
                help='Publish this hotfix branch to origin.')
        p.set_defaults(func=cls.run_publish)
        p.add_argument('version', nargs='?')

    @staticmethod
    def run_publish(args):
        gitflow = GitFlow()
        version = gitflow.name_or_current('hotfix', args.version)
        gitflow.start_transaction('publishing hotfix branch %s' % version)
        branch = gitflow.publish('hotfix', version)
        print
        print "Summary of actions:"
        print "- A new remote branch '%s' was created" % branch
        print "- The local branch '%s' was configured to track the remote branch" % branch
        print "- You are now on branch '%s'" % branch
        print


class SupportCommand(GitFlowCommand):
    @classmethod
    def register_parser(cls, parent):
        p = parent.add_parser('support', help='Manage your support branches.')
        p.add_argument('-v', '--verbose', action='store_true',
           help='be verbose (more output)')
        sub = p.add_subparsers(title='Actions')
        cls.register_list(sub)
        cls.register_start(sub)

    #- list
    @classmethod
    def register_list(cls, parent):
        p = parent.add_parser('list', help='List all support branches.')
        p.set_defaults(func=cls.run_list)
        p.add_argument('-v', '--verbose', action='store_true',
                help='Be verbose (more output).')

    @staticmethod
    def run_list(args):
        gitflow = GitFlow()
        gitflow.start_transaction()
        gitflow.list('support', 'version', use_tagname=True,
                     verbose=args.verbose)

    #- start
    @classmethod
    def register_start(cls, parent):
        p = parent.add_parser('start', help='Start a new support branch.')
        p.set_defaults(func=cls.run_start)
        p.add_argument('-F', '--fetch', action='store_true',
                help='Fetch from origin before performing local operation.')
        p.add_argument('name', action=NotEmpty)
        p.add_argument('base', nargs='?')

    @staticmethod
    def run_start(args):
        gitflow = GitFlow()
        # NB: `args.name` is required since the branch must not yet exist
        # :fixme: get default value for `base`
        gitflow.start_transaction('create support branch %s (from %s)' %
                (args.name, args.base))
        try:
            branch = gitflow.create('support', args.name, args.base,
                                    fetch=args.fetch)
        except BranchTypeExistsError:
            # printed in main()
            raise
        except Exception, e:
            die("Could not create support branch %r" % args.name,
                str(e))
        print
        print "Summary of actions:"
        print "- A new branch", branch, "was created, based on", args.base
        print "- You are now on branch", branch
        print ""


def main():
    parser = argparse.ArgumentParser(prog='git flow')
    placeholder = parser.add_subparsers(title='Subcommands')
    for cls in itersubclasses(GitFlowCommand):
        cls.register_parser(placeholder)
    args = parser.parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        raise SystemExit('Aborted by user request.')


if __name__ == '__main__':
    try:
        main()
    except GitflowError, e:
        raise SystemExit('Error: %s' %e)
