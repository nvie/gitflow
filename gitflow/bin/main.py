"""
export GITFLOW_DIR=$(dirname "$0")

usage() {
    echo "usage: git flow <subcommand>"
    echo
    echo "Available subcommands are:"
    echo "   init      Initialize a new git repo with support for the branching model."
    echo "   feature   Manage your feature branches."
    echo "   release   Manage your release branches."
    echo "   hotfix    Manage your hotfix branches."
    echo "   support   Manage your support branches."
    echo "   version   Shows version information."
    echo
    echo "Try 'git flow <subcommand> help' for details."
}

main() {
    if [ $# -lt 1 ]; then
        usage
        exit 1
    fi

    # load common functionality
    . "$GITFLOW_DIR/gitflow-common"

    # use the shFlags project to parse the command line arguments
    . "$GITFLOW_DIR/gitflow-shFlags"
    FLAGS_PARENT="git flow"
    FLAGS "$@" || exit $?
    eval set -- "${FLAGS_ARGV}"

    # sanity checks
    SUBCOMMAND="$1"; shift

    if [ ! -e "$GITFLOW_DIR/git-flow-$SUBCOMMAND" ]; then
        usage
        exit 1
    fi

    # run command
    . "$GITFLOW_DIR/git-flow-$SUBCOMMAND"
    FLAGS_PARENT="git flow $SUBCOMMAND"

    # test if the first argument is a flag (i.e. starts with '-')
    # in that case, we interpret this arg as a flag for the default
    # command
    SUBACTION="default"
    if [ "$1" != "" ] && ! echo "$1" | grep -q "^-"; then
        SUBACTION="$1"; shift
    fi
    if ! type "cmd_$SUBACTION" >/dev/null 2>&1; then
        warn "Unknown subcommand: '$SUBACTION'"
        usage
        exit 1
    fi

    # run the specified action
    cmd_$SUBACTION "$@"
}

main "$@"
"""
import argparse

from gitflow.commands import feature, release, init
COMMAND_CLASSES = (
   init.InitCommand,
   feature.FeatureCommand,
   release.ReleaseCommand,
)

def main():
    parser = argparse.ArgumentParser(prog='git flow')
    placeholder = parser.add_subparsers(title='Subcommands')
    for cls in COMMAND_CLASSES:
        cls().register_parser(placeholder)
    args = parser.parse_args()
    args.func(args)
