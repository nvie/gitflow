from gitflow import __version__


class VersionCommand(object):

    def register_parser(self, parent):
        p = parent.add_parser('version', help='Show the version of gitflow.')
        p.set_defaults(func=self.run)

    def run(self, args):
        print(__version__)
