class ReleaseCommand(object):

    def register_parser(self, parent):
        p = parent.add_parser('release', help='Manage your release branches.')
        p.add_argument('-v', '--verbose', action='store_true',
           help='be verbose (more output)')
        p.set_defaults(func=self.run)
        return p

    def run(self, args):
        print 'release ran'
        print(args)
