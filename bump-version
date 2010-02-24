#!/bin/sh
usage() {
	echo "usage: bump-version <version-id>"
}

if [ $# -ne 1 ]; then
	usage
	exit 1
fi

if ! sed 's/^GITFLOW_VERSION=.*$/GITFLOW_VERSION='$1'/g' git-flow-version > .git-flow-version.new; then
	echo "Could not replace GITFLOW_VERSION variable." >&2
	exit 2
fi

mv .git-flow-version.new git-flow-version
git add git-flow-version
git commit -m "Bumped version number to $1" git-flow-version
