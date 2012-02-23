#!/bin/sh
indent() {
    sed -e 's/^/     /'
}

gather_info() {
    pwd >&2
    mv dot_git .git | indent
    echo
    echo "- Config:"
    git config --list -f .git/config | indent
    echo
    echo "- Status:"
    git status | indent
    echo
    echo "- Branches:"
    git branch | indent
    echo
    echo "- Commit graph:"
    git log --graph --oneline --all --decorate | indent
    echo
    mv .git dot_git
}

collect() {
    echo "These are the available fixtures:"
    echo
    for x in *; do
        if [ ! -d $x ]; then
            continue
        fi
        echo "$x"
	echo "------------------"
        (cd $x; gather_info $x)
        echo
    done
}

collect > README.txt
