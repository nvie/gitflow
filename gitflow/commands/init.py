class InitCommand(object):

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
