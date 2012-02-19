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
from gitflow.core import GitFlow, die, info, BranchTypeExistsError
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


class VersionCommand(GitFlowCommand):
    def register_parser(self, parent):
        p = parent.add_parser('version', help='Show the version of gitflow.')
        p.set_defaults(func=self.run)

    def run(self, args):
        from gitflow import __version__
        print(__version__)


class StatusCommand(GitFlowCommand):
    def register_parser(self, parent):
        p = parent.add_parser('status', help='Show some status.')
        p.set_defaults(func=self.run)

    def run(self, args):
        gitflow = GitFlow()
        for name, hexsha, is_active_branch in gitflow.status():
            if is_active_branch:
                prefix = '*'
            else:
                prefix = ' '
            info('%s %s: %s' % (prefix, name, hexsha[:7]))


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
        self.register_list(sub)
        self.register_start(sub)
        self.register_finish(sub)
        self.register_publish(sub)
        self.register_track(sub)
        self.register_diff(sub)
        self.register_rebase(sub)
        self.register_checkout(sub)
        self.register_pull(sub)

    #- list
    def register_list(self, parent):
        p = parent.add_parser('list', help='List all feature branches.')
        p.set_defaults(func=self.run_list)
        p.add_argument('-v', '--verbose', action='store_true',
                help='Be verbose (more output).')

    def run_list(self, args):
        gitflow = GitFlow()
        gitflow.start_transaction()
        gitflow.list('feature', 'name', use_tagname=False,
                     verbose=args.verbose)

    #- start
    def register_start(self, parent):
        p = parent.add_parser('start', help='Start a new feature branch.')
        p.set_defaults(func=self.run_start)
        p.add_argument('-F', '--fetch', action='store_true',
                help='Fetch from origin before performing local operation.')
        p.add_argument('name')
        p.add_argument('base', nargs='?')

    def run_start(self, args):
        gitflow = GitFlow()
        # :todo: use_current_feature_branch_name(), wenn args.name == ""
        # :fixme: sh-vcersion doe ot require a clean working dr. why?
        gitflow.start_transaction('create feature branch %s (from %s)' % \
                (args.name, args.base))
        try:
            branch = gitflow.create('feature', args.name, args.base)
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
    def register_finish(self, parent):
        p = parent.add_parser('finish', help='Finish a feature branch.')
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

    def run_finish(self, args):
        gitflow = GitFlow()
        gitflow.start_transaction('finishing feature branch %s'
                % args.nameprefix)
        gitflow.finish('feature', args.nameprefix)

    #- publish
    def register_publish(self, parent):
        p = parent.add_parser('publish',
                help='Publish this feature branch to origin.')
        p.set_defaults(func=self.run_publish)
        p.add_argument('nameprefix')

    def run_publish(self, args): pass

    #- track
    def register_track(self, parent):
        p = parent.add_parser('track',
                help='Track a feature branch from origin.')
        p.set_defaults(func=self.run_track)
        p.add_argument('name')

    def run_track(self, args): pass

    #- diff
    def register_diff(self, parent):
        p = parent.add_parser('diff',
                help='Show a diff of changes since this feature branched off.')
        p.set_defaults(func=self.run_diff)
        p.add_argument('nameprefix', nargs='?')

    def run_diff(self, args): pass

    #- rebase
    def register_rebase(self, parent):
        p = parent.add_parser('rebase',
                help='Rebase a feature branch on top of develop.')
        p.set_defaults(func=self.run_rebase)
        p.add_argument('-i', '--interactive', action='store_true',
                help='Start an interactive rebase.')
        p.add_argument('nameprefix', nargs='?')

    def run_rebase(self, args): pass

    #- checkout
    def register_checkout(self, parent):
        p = parent.add_parser('checkout',
                help='Check out the given feature branch.')
        p.set_defaults(func=self.run_checkout)
        p.add_argument('nameprefix')

    def run_checkout(self, args): pass

    #- pull
    def register_pull(self, parent):
        p = parent.add_parser('pull',
                help='Pull a feature branch from a remote peer.')
        p.set_defaults(func=self.run_pull)
        p.add_argument('remote')
        p.add_argument('name', nargs='?')

    def run_pull(self, args): pass


class ReleaseCommand(GitFlowCommand):
    def register_parser(self, parent):
        p = parent.add_parser('release', help='Manage your release branches.')
        p.add_argument('-v', '--verbose', action='store_true',
           help='be verbose (more output)')
        sub = p.add_subparsers(title='Actions')
        self.register_list(sub)
        self.register_start(sub)
        self.register_finish(sub)
        self.register_publish(sub)
        self.register_track(sub)

    #- list
    def register_list(self, parent):
        p = parent.add_parser('list', help='List all release branches.')
        p.set_defaults(func=self.run_list)
        p.add_argument('-v', '--verbose', action='store_true',
                help='Be verbose (more output).')

    def run_list(self, args):
        gitflow = GitFlow()
        gitflow.start_transaction()
        gitflow.list('release', 'version', use_tagname=True,
                     verbose=args.verbose)

    #- start
    def register_start(self, parent):
        p = parent.add_parser('start', help='Start a new release branch.')
        p.set_defaults(func=self.run_start)
        p.add_argument('-F', '--fetch', action='store_true',
                       #:todo: get "origin" from config
                help='Fetch from origin before performing local operation.')
        p.add_argument('version')
        p.add_argument('base', nargs='?')

    def run_start(self, args):
        gitflow = GitFlow()
        gitflow.start_transaction('create release branch %s (from %s)' % \
                (args.version, args.base))
        try:
            branch = gitflow.create('release', args.version, args.base)
        except BranchTypeExistsError, e:
            die("There is an existing release branch (%s). "
                "Finish that one first." % e.args[0])
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
    def register_finish(self, parent):
        p = parent.add_parser('finish', help='Finish a release branch.')
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

    def run_finish(self, args): pass

    #- publish
    def register_publish(self, parent):
        p = parent.add_parser('publish',
                help='Publish this release branch to origin.')
        p.set_defaults(func=self.run_publish)
        p.add_argument('version')

    def run_publish(self, args): pass

    #- track
    def register_track(self, parent):
        p = parent.add_parser('track',
                help='Track a release branch from origin.')
        p.set_defaults(func=self.run_track)
        p.add_argument('version')

    def run_track(self, args): pass


class HotfixCommand(GitFlowCommand):
    def register_parser(self, parent):
        p = parent.add_parser('hotfix', help='Manage your hotfix branches.')
        p.add_argument('-v', '--verbose', action='store_true',
           help='be verbose (more output)')
        sub = p.add_subparsers(title='Actions')
        self.register_list(sub)
        self.register_start(sub)
        self.register_finish(sub)
        self.register_publish(sub)

    #- list
    def register_list(self, parent):
        p = parent.add_parser('list', help='List all hotfix branches.')
        p.set_defaults(func=self.run_list)
        p.add_argument('-v', '--verbose', action='store_true',
                help='Be verbose (more output).')

    def run_list(self, args):
        gitflow = GitFlow()
        gitflow.start_transaction()
        gitflow.list('hotfix', 'version', use_tagname=True,
                     verbose=args.verbose)

    #- start
    def register_start(self, parent):
        p = parent.add_parser('start', help='Start a new hotfix branch.')
        p.set_defaults(func=self.run_start)
        p.add_argument('-F', '--fetch', action='store_true',
                       #:todo: get "origin" from config
                help='Fetch from origin before performing local operation.')
        p.add_argument('version')
        p.add_argument('base', nargs='?')

    def run_start(self, args):
        gitflow = GitFlow()
        gitflow.start_transaction('create hotfix branch %s (from %s)' % \
                (args.version, args.base))
        try:
            branch = gitflow.create('hotfix', args.version, args.base)
        except BranchTypeExistsError, e:
            die("There is an existing hotfix branch (%s). "
                "Finish that one first." % e.args[0])
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
        print "     git flow hotfix finish ", args.version

    #- finish
    def register_finish(self, parent):
        p = parent.add_parser('finish', help='Finish a hotfix branch.')
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

    def run_finish(self, args): pass

    #- publish
    def register_publish(self, parent):
        p = parent.add_parser('publish',
                help='Publish this hotfix branch to origin.')
        p.set_defaults(func=self.run_publish)
        p.add_argument('version')

    def run_publish(self, args): pass


class SupportCommand(GitFlowCommand):
    def register_parser(self, parent):
        p = parent.add_parser('support', help='Manage your support branches.')
        p.add_argument('-v', '--verbose', action='store_true',
           help='be verbose (more output)')
        sub = p.add_subparsers(title='Actions')
        self.register_list(sub)
        self.register_start(sub)

    #- list
    def register_list(self, parent):
        p = parent.add_parser('list', help='List all support branches.')
        p.set_defaults(func=self.run_list)
        p.add_argument('-v', '--verbose', action='store_true',
                help='Be verbose (more output).')

    def run_list(self, args):
        gitflow = GitFlow()
        gitflow.start_transaction()
        gitflow.list('support', 'version', use_tagname=True,
                     verbose=args.verbose)

    #- start
    def register_start(self, parent):
        p = parent.add_parser('start', help='Start a new support branch.')
        p.set_defaults(func=self.run_start)
        p.add_argument('-F', '--fetch', action='store_true',
                help='Fetch from origin before performing local operation.')
        p.add_argument('name')
        p.add_argument('base', nargs='?')

    def run_start(self, args):
        gitflow = GitFlow()
        gitflow.start_transaction('create support branch %s (from %s)' %
                (args.name, args.base))
        try:
            branch = gitflow.create('support', args.name, args.base)
        except BranchTypeExistsError, e:
            die("There is an existing suport branch (%s). "
                "Finish that one first." % e.args[0])
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
        cls().register_parser(placeholder)
    args = parser.parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        die('', 'Aborted by user request.')


if __name__ == '__main__':
    main()
