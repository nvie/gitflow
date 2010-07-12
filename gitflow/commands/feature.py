from gitflow.assertions import require_gitflow_initialized
from gitflow.core import active_branch, feature_branches

class FeatureCommand(object):

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
        p = sub.add_parser('track', help='Track a feature branch from origin.')
        p.set_defaults(func=self.run_track)
        p.add_argument('name')

        # diff
        p = sub.add_parser('diff',
           help='Show a diff of all changes since this feature branches off.')
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
        for branch in feature_branches():
            is_active = active_branch().name == branch.fullname
            if is_active:
                prefix = '* '
            else:
                prefix = '  '
            if args.verbose:
                extra_info = ''
                print(prefix + branch.fullname + extra_info)
            else:
                print(prefix + branch.name)

    def run_start(self, args):
        print('Starting new FB!')
        print(args)
        print('-------------------')

    def run_finish(self, args): pass
    def run_publish(self, args): pass
    def run_track(self, args): pass
    def run_diff(self, args): pass
    def run_rebase(self, args): pass
    def run_checkout(self, args): pass
    def run_pull(self, args): pass
